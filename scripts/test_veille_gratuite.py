"""Tests hors ligne du filtrage gratuit et des garanties de provenance."""
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from datetime import datetime, timezone
sys.path.insert(0,str(Path(__file__).parent))
import veille_gratuite as free

class TestsGratuit(unittest.TestCase):
    def test_remotive_only_global_eligible_and_matching(self):
        now=datetime.now(timezone.utc).isoformat()
        jobs={'jobs':[
            {'title':'WASH Programme Coordinator', 'company_name':'Org A','url':'https://remotive.com/remote-jobs/wash',
             'description':'water supply sanitation, project management', 'candidate_required_location':'Worldwide','publication_date':now},
            {'title':'Hydrology Specialist', 'company_name':'Org B','url':'https://remotive.com/remote-jobs/hydrology',
             'description':'water resources climate', 'candidate_required_location':'United States only','publication_date':now},
            {'title':'Software Developer', 'company_name':'Org C','url':'https://remotive.com/remote-jobs/software',
             'description':'Code and build web apps', 'candidate_required_location':'Worldwide','publication_date':now},
        ]}
        result=free.from_remotive(jobs)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['org'],'Org A')
        self.assertEqual(result[0]['method'],'veille_gratuite')
        self.assertEqual(result[0]['verify'],'Non vérifiée')
    def test_news_remains_unverified_lead(self):
        now=datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
        root=ET.fromstring(f'''<rss><channel><item><title>Fully funded PhD hydrology position announced</title>
            <link>https://news.google.com/rss/articles/abc</link><description>University water research scholarship</description>
            <pubDate>{now}</pubDate><source>Research bulletin</source></item></channel></rss>''')
        result=free.from_news(root,'doctorats')
        self.assertEqual(len(result),1)
        self.assertIn('presse',result[0]['risk'])
        self.assertLessEqual(result[0]['match_score'],79)
        self.assertEqual(result[0]['verify'],'Non vérifiée')
    def test_expired_news_is_ignored(self):
        root=ET.fromstring('''<rss><channel><item><title>Hydrology PhD position</title><link>https://news.google.com/rss/articles/old</link><pubDate>Tue, 02 Jun 2020 10:00:00 GMT</pubDate></item></channel></rss>''')
        self.assertFalse(free.from_news(root,'doctorats'))
if __name__=='__main__':unittest.main(verbosity=2)
