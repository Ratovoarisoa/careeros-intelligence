"""Tests gratuits du pipeline, sans clé ni accès Internet."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).parent))
import veille_ia as v

class Tests(unittest.TestCase):
    def sample(self, **k):
        d={'org':'Université de test','title':'PhD eau souterraine','type':'Doctorat',
           'country':'Madagascar','location':'Tana',
           'deadline':(v.TODAY+timedelta(days=5)).isoformat(),
           'link':'https://university.example/jobs/hydrology?utm_source=ad',
           'source':'Site officiel','date_evidence':'Annonce','eligibility':'international',
           'funding':'bourse','fit':['hydraulique'],'risk':'À vérifier',
           'cv_focus':'qualité eau','next':'relire','match_score':85}
        return {**d,**k}
    def test_canonical(self):
        self.assertEqual(v.canon_url(self.sample()['link']), 'https://university.example/jobs/hydrology')
        for link in ['http://university.example','https://127.0.0.1/jobs','https://localhost/path',
                     'https://user:pass@university.example','javascript:alert(1)']:
            self.assertFalse(v.canon_url(link))
    def test_fresh_and_expired(self):
        self.assertIsNotNone(v.validate(self.sample(),'doctorats'))
        self.assertIsNone(v.validate(self.sample(deadline=(v.TODAY-timedelta(days=1)).isoformat()),'doctorats'))
        self.assertIsNone(v.validate(self.sample(match_score=10),'doctorats'))
    def test_same_offer(self):
        a=self.sample();b=self.sample(link='https://university.example/jobs/hydrology')
        self.assertTrue(v.same_offer(a,b))
    def test_build_retains_old(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t);(r/'site/data').mkdir(parents=True)
            (r/'baseline.json').write_text('[]',encoding='utf8')
            a=v.validate(self.sample(),'doctorats')
            feed=v.build_feed(r,{'doctorats':[a]})
            self.assertEqual(feed['new_count'],1)
            (r/'site/data/veille.json').write_text(json.dumps(feed),encoding='utf8')
            later=v.build_feed(r,{'doctorats':[a]})
            self.assertEqual(later['new_count'],0)
            self.assertEqual(len(later['items']),1)
            self.assertEqual(later['items'][0]['first_seen'],feed['items'][0]['first_seen'])
    def test_static_app_no_contacts_or_private_cv(self):
        root=Path(__file__).parent.parent
        source=(root/'site/index.html').read_text(encoding='utf8')
        self.assertIn('CareerOS',source)
        self.assertNotIn('lucaedwinratovoarisoa@gmail.com',source)
        self.assertEqual(len(list((root/'site').rglob('*.pdf'))),0)
        self.assertEqual(len(list((root/'site').rglob('*.docx'))),0)

if __name__=='__main__':unittest.main(verbosity=2)
