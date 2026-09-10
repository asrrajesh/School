import unittest
from uuid import uuid4

from bson import ObjectId

from database.db import get_db, save_scanned_chapter


class ScannedChapterTests(unittest.TestCase):
    def test_save_scanned_chapter(self):
        content = f"integration-test-{uuid4()}"
        result = save_scanned_chapter("I", "Science", "1", content, "integration-test")
        self.assertTrue(result["success"])

        collection = get_db().scanned_chapters
        inserted_id = ObjectId(result["id"])
        try:
            record = collection.find_one({"_id": inserted_id})
            self.assertIsNotNone(record)
            self.assertEqual(record["class"], "I")
            self.assertEqual(record["subject"], "Science")
            self.assertEqual(record["chapter"], "1")
            self.assertEqual(record["content"], content)
        finally:
            collection.delete_one({"_id": inserted_id})


if __name__ == "__main__":
    unittest.main()
