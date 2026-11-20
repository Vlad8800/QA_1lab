"""Exercise failure modes of the CI review-date gate using isolated fixtures."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import date
import unittest

spec=importlib.util.spec_from_file_location('review',Path(__file__).with_name('check_review_dates.py'))
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)

class ReviewPolicyTests(unittest.TestCase):
    def test_expired_page_blocks_delivery(self):
        with TemporaryDirectory() as tmp:
            old=review.ROOT; review.ROOT=Path(tmp)
            try:
                (review.ROOT/'docs').mkdir()
                for name in ['README.md','CONTRIBUTING.md','CHANGELOG.md']:
                    (review.ROOT/name).write_text('---\nowner: owner\nstatus: published\nreview_date: 2026-11-19\n---\n# Example\n')
                result=review.audit(date(2026,11,20))
                self.assertEqual(3,len(result['overdue']))
                self.assertEqual([],result['errors'])
            finally:review.ROOT=old

    def test_deprecated_page_requires_valid_replacement(self):
        with TemporaryDirectory() as tmp:
            old=review.ROOT;review.ROOT=Path(tmp)
            try:
                (review.ROOT/'docs').mkdir()
                for name in ['README.md','CONTRIBUTING.md','CHANGELOG.md']:
                    (review.ROOT/name).write_text('---\nowner: owner\nstatus: deprecated\nreview_date: 2026-11-19\nreplacement: missing.md\n---\n# Example\n')
                result=review.audit(date(2026,11,20))
                self.assertEqual(3,len(result['errors']))
                self.assertEqual([],result['overdue'])
            finally:review.ROOT=old

if __name__=='__main__':unittest.main()
