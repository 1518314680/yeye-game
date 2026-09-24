"""One-use voucher lottery. All odds and inventory are decided on the server."""

import argparse
import base64
import hashlib
import os
import secrets
import sqlite3
from contextlib import contextmanager, nullcontext
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request


# code, display name, reward, maximum winners, initial probability (percent)
PRIZES = (
    ("first", "一等奖", "888元现金", 2, 0),
    ("second", "二等奖", "328/288免单", 4, 0),
    ("third", "三等奖", "88元现金", 6, 5),
    ("fourth", "四等奖", "50元现金", 10, 10),
    ("fifth", "五等奖", "续单20元立减券", 20, 25),
    ("thanks", "谢谢惠顾", "下次好运", None, 60),
)
PRIZE_BY_CODE = {prize[0]: prize for prize in PRIZES}
DEFAULT_DB = Path(__file__).resolve().parent / "data" / "lottery.sqlite3"
def normalized_code(value):
    if not isinstance(value, str):
        return None
    value = value.strip().upper().replace("-", "").replace(" ", "")
    if len(value) != 22 or not value.startswith("YY"):
        return None
    return value if all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for c in value[2:]) else None


def hash_code(value):
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def generate_code():
    part = base64.b32encode(secrets.token_bytes(12)).decode("ascii").rstrip("=")
    return "YY-" + "-".join(part[i:i + 5] for i in range(0, 20, 5))


def display_code(value):
    return "YY-" + "-".join(value[i:i + 5] for i in range(2, 22, 5))


@contextmanager
def database(path):
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        with db:
            yield db
    finally:
        db.close()


def init_db(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with database(path) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""CREATE TABLE IF NOT EXISTS inventory (
            prize_code TEXT PRIMARY KEY,
            quota INTEGER NOT NULL CHECK (quota >= 0),
            awarded INTEGER NOT NULL DEFAULT 0 CHECK (awarded BETWEEN 0 AND quota)
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS vouchers (
            id INTEGER PRIMARY KEY,
            code_hash TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY,
            voucher_id INTEGER NOT NULL UNIQUE REFERENCES vouchers(id),
            prize_code TEXT NOT NULL,
            drawn_at TEXT NOT NULL
        )""")
        for code, _, _, quota, _ in PRIZES:
            if quota is not None:
                db.execute("INSERT OR IGNORE INTO inventory (prize_code, quota) VALUES (?, ?)", (code, quota))


def stock_snapshot(db):
    return {row["prize_code"]: row for row in db.execute("SELECT * FROM inventory")}


def choose_prize(stock, roll):
    # Exhausted ranges become "thanks". Other ranges never expand.
    cumulative = 0
    for code, _, _, quota, rate in PRIZES:
        if code == "thanks":
            return "thanks"
        cumulative += rate
        if roll < cumulative:
            row = stock[code]
            return code if row["awarded"] < quota else "thanks"
    return "thanks"


def create_app(db_path=None):
    app = Flask(__name__)
    path = str(db_path or os.environ.get("LOTTERY_DB_PATH", DEFAULT_DB))
    init_db(path)

    @app.get("/api/lottery/prizes")
    def prizes():
        with database(path) as db:
            stock = stock_snapshot(db)
        items = []
        active = 0
        for code, name, description, quota, rate in PRIZES:
            remaining = None if quota is None else stock[code]["quota"] - stock[code]["awarded"]
            current = rate if remaining is None or remaining > 0 else 0
            if code in ("third", "fourth", "fifth"):
                active += current
            items.append({"code": code, "name": name, "description": description,
                          "quota": quota, "remaining": remaining, "initialRate": rate,
                          "currentRate": current})
        items[-1]["currentRate"] = 100 - active
        response = jsonify({"prizes": items})
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.post("/api/lottery/draw")
    def draw():
        data = request.get_json(silent=True) or {}
        code = normalized_code(data.get("voucherCode"))
        if code is None:
            return jsonify({"error": "请输入有效的兑奖券码"}), 400

        with database(path) as db:
            db.execute("BEGIN IMMEDIATE")
            voucher = db.execute("SELECT id FROM vouchers WHERE code_hash = ?", (hash_code(code),)).fetchone()
            if voucher is None:
                return jsonify({"error": "券码不存在，请检查后重试"}), 404
            previous = db.execute(
                "SELECT id, prize_code, drawn_at FROM draws WHERE voucher_id = ?", (voucher["id"],)
            ).fetchone()
            if previous:
                response = jsonify({"error": "该兑奖码已经被使用过"})
                response.status_code = 409
                response.headers["Cache-Control"] = "no-store"
                return response
            result = choose_prize(stock_snapshot(db), secrets.randbelow(100))
            drawn_at = datetime.now(timezone.utc).isoformat()
            if result != "thanks":
                updated = db.execute(
                    "UPDATE inventory SET awarded = awarded + 1 "
                    "WHERE prize_code = ? AND awarded < quota", (result,)
                )
                if updated.rowcount != 1:
                    raise RuntimeError("Prize inventory could not be updated")
            row = db.execute(
                "INSERT INTO draws (voucher_id, prize_code, drawn_at) VALUES (?, ?, ?)",
                (voucher["id"], result, drawn_at),
            )
            draw_id = row.lastrowid

        prize = PRIZE_BY_CODE[result]
        response = jsonify({"drawId": draw_id, "prizeCode": result,
                            "prizeName": prize[1], "description": prize[2],
                            "drawnAt": drawn_at,
                            "redemptionCode": display_code(code) if result != "thanks" else None,
                            "voucherCode": display_code(code)})
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.post("/api/lottery/record")
    def record():
        data = request.get_json(silent=True) or {}
        code = normalized_code(data.get("voucherCode"))
        if code is None:
            return jsonify({"error": "请输入有效的抽奖码"}), 400
        with database(path) as db:
            row = db.execute(
                "SELECT draws.prize_code, draws.drawn_at FROM vouchers LEFT JOIN draws "
                "ON draws.voucher_id = vouchers.id WHERE vouchers.code_hash = ?",
                (hash_code(code),),
            ).fetchone()
        if row is None:
            return jsonify({"error": "未找到该抽奖码"}), 404
        if row["prize_code"] is None:
            response = jsonify({"status": "unused", "voucherCode": display_code(code),
                                "message": "该抽奖码还未使用"})
            response.headers["Cache-Control"] = "no-store"
            return response
        prize = PRIZE_BY_CODE[row["prize_code"]]
        response = jsonify({"status": "drawn", "prizeCode": row["prize_code"],
                            "prizeName": prize[1], "description": prize[2],
                            "drawnAt": row["drawn_at"],
                            "voucherCode": display_code(code),
                            "redemptionCode": display_code(code) if row["prize_code"] != "thanks" else None})
        response.headers["Cache-Control"] = "no-store"
        return response

    return app


def main():
    parser = argparse.ArgumentParser(description="抽奖券管理")
    parser.add_argument("command", choices=("init", "generate", "report"))
    parser.add_argument("count", nargs="?", type=int, default=1)
    parser.add_argument("--output", type=Path, help="将生成的抽奖码写入 TXT 文件，每行一个；已有文件不会覆盖")
    args = parser.parse_args()
    if args.output is not None and args.command != "generate":
        parser.error("--output 仅可与 generate 命令一起使用")
    path = os.environ.get("LOTTERY_DB_PATH", str(DEFAULT_DB))
    init_db(path)
    if args.command == "init":
        print(f"数据库已初始化：{path}")
    elif args.command == "generate":
        if not 1 <= args.count <= 10000:
            parser.error("每次生成数量须在 1 到 10000 之间")
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
        destination = args.output.open("x", encoding="utf-8", newline="\n") if args.output else nullcontext(None)
        with destination as output:
            with database(path) as db:
                codes = []
                for _ in range(args.count):
                    while True:
                        code = generate_code()
                        try:
                            db.execute(
                                "INSERT INTO vouchers (code_hash, created_at) VALUES (?, ?)",
                                (hash_code(normalized_code(code)), datetime.now(timezone.utc).isoformat()),
                            )
                            codes.append(code)
                            if output is not None:
                                output.write(code + "\n")
                            break
                        except sqlite3.IntegrityError:
                            continue
                if output is not None:
                    output.flush()
                    os.fsync(output.fileno())
        if args.output is None:
            print("\n".join(codes))
        else:
            print(f"已生成 {len(codes)} 个抽奖码，文件：{args.output.resolve()}")
    elif args.command == "report":
        with database(path) as db:
            for code, name, _, quota, _ in PRIZES:
                if quota is not None:
                    row = db.execute(
                        "SELECT awarded FROM inventory WHERE prize_code = ?", (code,)
                    ).fetchone()
                    print(f"{name}: {row['awarded']}/{quota}")
            total = db.execute("SELECT COUNT(*) FROM draws WHERE prize_code='thanks'").fetchone()[0]
            print(f"谢谢惠顾: {total}")


if __name__ == "__main__":
    main()
else:
    app = create_app()
