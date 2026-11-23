#!/usr/bin/env python3
"""Veille CareerOS sans clé API: Remotive + flux d'actualité RSS.

Les éléments sont des pistes NON vérifiées, jamais présentées comme des offres certifiées.
Dépendances: Python standard library uniquement. Aucun service IA externe.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
import hashlib
import json
import re
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import veille_ia as core

ROOT = Path(__file__).resolve().parent.parent
AGENT='CareerOSIntelligence/2.1 (personal opportunity discovery; links to sources)'
SEARCHES = [
    ('doctorats', '"fully funded" "PhD" hydrology water university'),
    ('doctorats', '"PhD position" groundwater wastewater climate funded'),
    ('bourses', '"Erasmus Mundus" water scholarships 2027 applications'),
    ('bourses', '"water diplomacy" fellowship scholarships applications'),
    ('emplois', '"WASH" engineer Madagascar recruitment vacancy'),
    ('emplois', '"water sanitation" project coordinator jobs NGO'),
]
WATER = ('wash','water','wastewater','hydrol','hydraul','groundwater','sanitat','climat','watershed',
         'inondation','flood','drinking water','eau potable','assainissement','hydrogeol','water resource')
ROLE = ('engineer','specialist','officer','manager','coordinator','consultant','program','programme',
        'research','doctor','phd','fellow','scholarship','bourse','intern','stage','technicien')
RESTRICTED = ('united states only','us only','usa only','u.s. only','canada only','uk only',
              'eu only','europe only','united kingdom only','us-based candidates only')
GLOBAL = ('worldwide','global','anywhere','africa','madagascar','international')


def fetch_json(url: str, timeout: int = 24):
    req=Request(url,headers={'User-Agent':AGENT,'Accept':'application/json'})
    with urlopen(req,timeout=timeout) as r:
        return json.loads(r.read(1_500_000).decode('utf-8'))


def fetch_xml(url: str, timeout: int = 24):
    req=Request(url,headers={'User-Agent':AGENT,'Accept':'application/rss+xml,application/xml,text/xml'})
    with urlopen(req,timeout=timeout) as r:
        return ET.fromstring(r.read(1_500_000))


def plain(html: str) -> str:
    return re.sub(r'\s+',' ',unescape(re.sub(r'<[^>]*>',' ',html or ''))).strip()


def recent(when: str, max_days: int = 35) -> bool:
    if not when:
        return True
    try:
        if re.match(r'^\d{4}-\d\d-\d\d',when):
            d=datetime.fromisoformat(when.replace('Z','+00:00'))
        else:
            d=parsedate_to_datetime(when)
        if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
        days=(datetime.now(timezone.utc)-d).days
        return -2 <= days <= max_days
    except (ValueError,TypeError,OverflowError):return True


def rating(title: str, description: str, kind: str, is_news: bool = False) -> tuple[int,list[str]]:
    t=title.lower();desc=description.lower(); combined=t+' '+desc
    if not any(w in combined for w in WATER):return 0,[]
    important=[('WASH / eau et assainissement',('wash','drinking water','water supply','eau potable')),
               ('Hydrologie / hydraulique',('hydrol','hydraul','watershed','groundwater')),
               ('Qualité des eaux / traitement',('wastewater','water quality','effluent','water treatment')),
               ('Climat / résilience',('climate','climat','resilience','flood','inondation')),
               ('Gestion de projets',('project manager','program coordinator','project coordinator','project officer'))]
    hits=[label for label,words in important if any(w in combined for w in words)]
    in_title=any(w in t for w in WATER)
    score=38+(20 if in_title else 2)+min(18,6*len(hits))
    if any(w in t for w in ('wash','hydrol','hydraul','groundwater','wastewater','sanitation','water supply')):score+=9
    if kind=='Doctorat' and any(x in combined for x in ('funded','scholarship','stipend','studentship','salary')):score+=10
    if kind in ('Master','Bourse','Programme') and 'scholarship' in combined:score+=8
    if kind in ('Emploi','Consultance') and any(x in combined for x in ('project','program','officer','manager','coordinator')):score+=5
    if is_news:score=min(score,79)
    return min(91,score),hits[:4]


def candidate(*,title:str,org:str,kind:str,url:str,description:str='',country:str='International',
              location:str='À préciser',source:str='',funding:str='Non précisé',
              eligibility:str='À confirmer auprès de l’organisme',risk:str='',is_news:bool=False,deadline:str=''):
    title=plain(title)[:170];org=plain(org)[:110];url=core.canon_url(url)
    if not all((title,org,url)):return None
    score,hits=rating(title,description,kind,is_news)
    if score<58:return None
    raw={'title':title,'org':org,'type':kind,'link':url,'country':country,'location':location,
         'deadline':deadline,'source':source,'date_evidence':'','eligibility':eligibility,
         'funding':funding,'fit':hits,'risk':risk or 'Annonce et critères à vérifier sur le site source.',
         'cv_focus':('CV recherche : étude de pollution Ikopa, analyse COD/DBO5/MES, QGIS, méthodes et hydrologie.'
                     if kind=='Doctorat' else 'CV WASH/partenariats : CARE SPRING, MadAvance, suivi de 581 points d’eau.'),
         'next':'Vérifier la page du recruteur, les critères pour un candidat malagasy et les dates limites.',
         'match_score':score}
    c=core.validate(raw,'doctorats' if kind=='Doctorat' else 'bourses' if kind in ('Bourse','Master','Programme') else 'emplois')
    if c:
        c['method']='veille_gratuite'
        c['auto_discovered']=True
        c['risk']=raw['risk']
        c['fit']=hits
        c['verify']='Non vérifiée'
    return c


def from_remotive(data: dict) -> list[dict]:
    rows=[]
    for j in (data.get('jobs') or []):
        title=plain(str(j.get('title','')))
        description=plain(str(j.get('description','')))[:3200]
        if not recent(str(j.get('publication_date','')),35):continue
        if not any(w in (title+' '+description).lower() for w in WATER):continue
        location=str(j.get('candidate_required_location','Worldwide'))
        loc=location.lower()
        if any(x in loc for x in RESTRICTED):continue
        # Only automatically recommend remote jobs with broad eligibility.
        # Exact eligibility still must be verified with the company.
        if not any(x in loc for x in GLOBAL) and loc.strip() not in ('','remote','anywhere in the world'):
            continue
        kind='Consultance' if any(x in title.lower() for x in ('consultant','contractor','consultancy')) else 'Emploi'
        c=candidate(title=title,org=str(j.get('company_name') or 'Employeur non indiqué'),kind=kind,
                    url=str(j.get('url') or ''),description=description,country='International',
                    location='Remote — '+location,source='Remotive (offre distante)',
                    funding=str(j.get('salary') or 'Rémunération non publiée'),
                    eligibility='Zone indiquée : '+location+' ; confirmer l’éligibilité Madagascar',
                    risk='Remotive est un agrégateur. La zone géographique, la disponibilité et les critères doivent être vérifiés sur l’annonce de l’employeur.')
        if c:rows.append(c)
    return rows


def from_news(root: ET.Element,track:str) -> list[dict]:
    rows=[];kind={'doctorats':'Doctorat','bourses':'Bourse','emplois':'Emploi'}[track]
    for el in root.findall('.//item')[:40]:
        title=plain(el.findtext('title',''))
        link=el.findtext('link','')
        summary=plain(el.findtext('description',''))[:1000]
        if not recent(el.findtext('pubDate',''),18):continue
        t=title.lower()
        if not any(w in t for w in WATER):continue
        if not any(w in t for w in ('phd','position','studentship','funded','scholarship','fellowship',
                                    'application','vacancy','recruit','job','bourse','water diplomacy','emploi')):continue
        source=el.find('source'); publisher=plain(source.text or '') if source is not None else 'Éditeur non précisé'
        c=candidate(title=title,org=publisher or 'Source non confirmée',kind=kind,url=link,
                    description=summary+' '+title,country='À vérifier',source='Google News RSS — piste indirecte',
                    eligibility='Nationalité et conditions non vérifiées',
                    risk='Piste identifiée dans un article de presse (pas une annonce de recrutement). Ouvrir le lien puis retrouver l’offre sur le site officiel avant de candidater.',
                    is_news=True)
        if c:rows.append(c)
    return rows


def discover() -> tuple[dict[str,list[dict]],list[str],int]:
    collected={'emplois':[],'doctorats':[],'bourses':[]};errors=[];success=0
    for search in ('water','WASH','environment'):
        try:
            data=fetch_json('https://remotive.com/api/remote-jobs?'+urlencode({'search':search,'limit':100}))
            collected['emplois'].extend(from_remotive(data));success+=1
        except Exception as e:errors.append('Remotive '+search+': '+str(e)[:130])
    for track,q in SEARCHES:
        try:
            url='https://news.google.com/rss/search?'+urlencode({'q':q+' when:30d','hl':'en','gl':'US','ceid':'US:en'})
            feed=fetch_xml(url)
            collected[track].extend(from_news(feed,track));success+=1
        except Exception as e:errors.append('RSS '+track+': '+str(e)[:130])
    for cat,rows in collected.items():
        dedup=[]
        for c in sorted(rows,key=lambda x:-x['match_score']):
            if not any(core.same_offer(c,x) for x in dedup):dedup.append(c)
        collected[cat]=dedup[:22]
    return collected,errors,success


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,default=ROOT)
    ap.add_argument('--demo',action='store_true',help='Ne fait aucune requête réseau')
    args=ap.parse_args()
    if args.demo:
        fake={'jobs':[{'title':'WASH Project Coordinator','company_name':'TEST',
              'url':'https://remotive.com/remote-jobs/test/wash-coordinator','description':'Community water and sanitation management',
              'candidate_required_location':'Worldwide','publication_date':datetime.now(timezone.utc).isoformat()}]}
        assert from_remotive(fake), 'Le classement offline devrait trouver le WASH Coordinator'
        print('Veille gratuite : autotest offline OK; aucune offre fictive enregistrée')
        return
    groups,errors,success=discover()
    if success==0:
        print('ERREUR: aucune source accessible; conservation du dernier flux existant. '+' ; '.join(errors),file=sys.stderr)
        raise SystemExit(2)
    feed=core.build_feed(args.root,groups)
    feed['method']='veille_gratuite'
    feed['status']='ok' if not errors else 'partial'
    feed['sources_ok']=success
    feed['sources_failed']=len(errors)
    feed['disclaimer']='Veille automatique gratuite : classement par mots-clés, PAS une analyse IA. Annonces et articles non vérifiés, disponibilité/éligibilité à confirmer sur les sites officiels.'
    out_root=args.root/'site' if (args.root/'site').is_dir() else args.root
    core.write_json_atomic(out_root/'data'/'veille.json',json.dumps(feed,ensure_ascii=False,indent=2)+'\n')
    js='window.CAREEROS_DAILY_FEED = '+json.dumps(feed,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+';\n'
    core.write_json_atomic(out_root/'data'/'veille.js',js)
    print(f"Veille gratuite : {success} sources OK, {len(errors)} échecs, {feed['total_discovered']} pistes, {feed['new_count']} nouvelles")

if __name__=='__main__':main()
