import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch


_import_db = tempfile.TemporaryDirectory()
_previous_db = os.environ.get("LOTTERY_DB_PATH")
os.environ["LOTTERY_DB_PATH"] = str(Path(_import_db.name) / "import.sqlite3")

from lottery_backend import app as lottery  # noqa: E402

if _previous_db is None:
    del os.environ["LOTTERY_DB_PATH"]
else:
    os.environ["LOTTERY_DB_PATH"] = _previous_db


class LotteryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "test.sqlite3")
        self.app = lottery.create_app(self.path)
        self.app.testing = True

    def tearDown(self):
        self.temp.cleanup()

    def add_voucher(self):
        code = lottery.generate_code()
        with lottery.database(self.path) as db:
            db.execute(
                "INSERT INTO vouchers (code_hash, created_at) VALUES (?, ?)",
                (lottery.hash_code(lottery.normalized_code(code)), "test"),
            )
        return code

    def draw(self, code):
        with self.app.test_client() as client:
            return client.post("/api/lottery/draw", json={"voucherCode": code})

    def test_fixed_ranges_and_exhaustion(self):
        with lottery.database(self.path) as db:
            stock = lottery.stock_snapshot(db)
        results = {lottery.choose_prize(stock, roll) for roll in range(100)}
        self.assertEqual(results, {"third", "fourth", "fifth", "thanks"})
        self.assertEqual([lottery.choose_prize(stock, x) for x in (0, 4, 5, 14, 15, 39, 40, 99)],
                         ["third", "third", "fourth", "fourth", "fifth", "fifth", "thanks", "thanks"])
        with lottery.database(self.path) as db:
            db.execute("UPDATE inventory SET awarded = quota WHERE prize_code = 'third'")
            stock = lottery.stock_snapshot(db)
        self.assertEqual(lottery.choose_prize(stock, 0), "thanks")
        with self.app.test_client() as client:
            prize_list = client.get("/api/lottery/prizes").json["prizes"]
        self.assertEqual(prize_list[0]["currentRate"], 0)
        self.assertNotIn("sixth", [prize["code"] for prize in prize_list])
        self.assertEqual(prize_list[-1]["currentRate"], 65)
        with lottery.database(self.path) as db:
            db.execute("UPDATE inventory SET awarded = quota WHERE prize_code IN ('fourth', 'fifth')")
        with self.app.test_client() as client:
            exhausted = client.get("/api/lottery/prizes").json["prizes"]
        self.assertEqual(exhausted[-1]["currentRate"], 100)

    def test_reusing_voucher_is_rejected_and_original_result_remains_queryable(self):
        code = self.add_voucher()
        with patch.object(lottery.secrets, "randbelow", return_value=0):
            first = self.draw(code)
        with patch.object(lottery.secrets, "randbelow", return_value=70):
            second = self.draw(code)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json["prizeCode"], "third")
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json["error"], "该兑奖码已经被使用过")
        with self.app.test_client() as client:
            record = client.post("/api/lottery/record", json={"voucherCode": code})
        self.assertEqual(record.status_code, 200)
        self.assertEqual(record.json["prizeCode"], first.json["prizeCode"])
        self.assertEqual(record.json["redemptionCode"], code)
        with lottery.database(self.path) as db:
            awarded = db.execute("SELECT awarded FROM inventory WHERE prize_code='third'").fetchone()[0]
            draws = db.execute("SELECT COUNT(*) FROM draws").fetchone()[0]
        self.assertEqual((awarded, draws), (1, 1))

    def test_record_lookup_before_and_after_draw(self):
        code = self.add_voucher()
        with self.app.test_client() as client:
            unused = client.post("/api/lottery/record", json={"voucherCode": code})
        self.assertEqual(unused.json["status"], "unused")
        self.assertEqual(unused.json["message"], "该抽奖码还未使用")
        with patch.object(lottery.secrets, "randbelow", return_value=0):
            self.draw(code)
        with self.app.test_client() as client:
            used = client.post("/api/lottery/record", json={"voucherCode": code})
        self.assertEqual(used.json["status"], "drawn")
        self.assertEqual(used.json["prizeCode"], "third")
        self.assertEqual(used.json["redemptionCode"], code)
        self.assertIsNotNone(used.json["drawnAt"])

    def test_thanks_record_has_no_redemption_code(self):
        code = self.add_voucher()
        with patch.object(lottery.secrets, "randbelow", return_value=70):
            self.draw(code)
        with self.app.test_client() as client:
            result = client.post("/api/lottery/record", json={"voucherCode": code})
        self.assertEqual(result.json["status"], "drawn")
        self.assertEqual(result.json["prizeCode"], "thanks")
        self.assertIsNone(result.json["redemptionCode"])

    def test_prize_rates_total_forty_percent(self):
        with self.app.test_client() as client:
            prizes = client.get("/api/lottery/prizes").json["prizes"]
        self.assertEqual({item["code"]: item["currentRate"] for item in prizes}, {
            "first": 0, "second": 0, "third": 5, "fourth": 10, "fifth": 25, "thanks": 60,
        })

    def test_concurrent_draws_do_not_exceed_inventory(self):
        codes = [self.add_voucher(), self.add_voucher()]
        with lottery.database(self.path) as db:
            db.execute("UPDATE inventory SET awarded = quota - 1 WHERE prize_code='third'")
        with patch.object(lottery.secrets, "randbelow", return_value=0):
            with ThreadPoolExecutor(max_workers=2) as pool:
                responses = list(pool.map(self.draw, codes))
        self.assertEqual({response.json["prizeCode"] for response in responses}, {"third", "thanks"})
        with lottery.database(self.path) as db:
            awarded = db.execute("SELECT awarded, quota FROM inventory WHERE prize_code='third'").fetchone()
        self.assertEqual(awarded["awarded"], awarded["quota"])


if __name__ == "__main__":
    unittest.main()
