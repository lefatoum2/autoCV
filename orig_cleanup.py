# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.4.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # convert existing pub list to csv
#

import pandas as pd
from Bio import Entrez
import json
import os


# +
retmax = 1000
handle = Entrez.esearch(db="pubmed", retmax=retmax,term='poldrack-r')
record = Entrez.read(handle)
handle.close()
pmids=[int(i) for i in record['IdList']]
print('found %d records' % len(pmids))


# -

handle = Entrez.efetch(db="pubmed", id=",".join(['%d'%i for i in pmids]),
                       retmax=retmax,retmode="xml")
records=Entrez.read(handle)


print('found %d records'%len(records['PubmedArticle']))



# load various links
osf_df = pd.read_csv('osf_links.csv', index_col=0)
osf_links = {}
for i in osf_df.index:
    osf_links[i] = osf_df.loc[i, 'url']
osf_links

code_df = pd.read_csv('code_links.csv', index_col=0)
code_links = {}
for i in code_df.index:
    code_links[i] = code_df.loc[i, 'url']
code_links

# +
pubs = {}

for i in records['PubmedArticle']:
    pmid=int(i['MedlineCitation']['PMID'])
    if 'Year' in i['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate']:
        year = i['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate']['Year']
    elif 'MedlineDate' in i['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate']:
        year = i['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate']['MedlineDate'].split(' ')[0]
    else:
        print('no year - skipping', pmid)

    if not year in pubs:
        pubs[year] = {}
    pubs[year][pmid] = {}
    
    authorlist = []
    if 'AuthorList' in i['MedlineCitation']['Article']:
        for author in i['MedlineCitation']['Article']['AuthorList']:
            if 'LastName' in author and 'Initials' in author:
                authorlist.append(' '.join([author['LastName'], author['Initials']]))
        pubs[year][pmid]['authors'] = ', '.join(authorlist)
    if 'Volume' in i['MedlineCitation']['Article']['Journal']['JournalIssue']:
        pubs[year][pmid]['volume'] = i['MedlineCitation']['Article']['Journal']['JournalIssue']['Volume']
    else:
        pubs[year][pmid]['volume'] = ''

    pubs[year][pmid]['title'] = i['MedlineCitation']['Article']['ArticleTitle']

    if 'Pagination' in i['MedlineCitation']['Article']:
        pubs[year][pmid]['pages'] = i['MedlineCitation']['Article']['Pagination']['MedlinePgn']

    pubs[year][pmid]['journal'] = i['MedlineCitation']['Article']['Journal']['ISOAbbreviation']
    # try to get PMC 
    for j in i['PubmedData']['ArticleIdList']:
        if j.attributes['IdType'] == 'pmc':
            pubs[year][pmid]['PMC'] = str(j)
        if j.attributes['IdType'] == 'doi':
            pubs[year][pmid]['DOI'] = str(j)
    if pmid in osf_links:
        pubs[year][pmid]['OSF'] = osf_links[pmid]
        
    if pmid in code_links:
        pubs[year][pmid]['code'] = code_links[pmid]
        


# +
# load addtional pubs from json - TBD

if os.path.exists('additional_pubs.csv'):
    pass
    # TBD

# -

# # convert to latex
#

# +
# sort by year

years = list(pubs.keys())
years.sort(reverse=True)

latex_lines = []
for year in years:
    latex_lines.append('\\subsection*{%s}' % year)
    for pmid in pubs[year]:
        if len(pubs[year][pmid]['authors'].split(','))>10:
            authorlist = pubs[year][pmid]['authors'].split(',')[0] + ', et al.'
        else:
            authorlist = pubs[year][pmid]['authors']
        line = authorlist +\
            ' (%s). ' % year +\
            pubs[year][pmid]['title'] +\
            ' \\textit{%s' % pubs[year][pmid]['journal']
        if pubs[year][pmid]['volume'] != '':
            line += ', %s}' % pubs[year][pmid]['volume']
        else:
            line += '}'
        if 'pages' in pubs[year][pmid]:
            line += ', %s' % pubs[year][pmid]['pages']
        line += '.'
        
        if 'PMC' in pubs[year][pmid]:
            line += ' \\href{https://www.ncbi.nlm.nih.gov/pmc/articles/%s}{OA}' % pubs[year][pmid]['PMC']
            
        if 'OSF' in pubs[year][pmid]:
            line += ' \\href{%s}{OSF}' % pubs[year][pmid]['OSF']
            
        if 'code' in pubs[year][pmid]:
            line += ' \\href{%s}{Code}' % pubs[year][pmid]['code']

        if 'DOI' in pubs[year][pmid]:
            line += ' DOI: %s' % pubs[year][pmid]['DOI']
        
        line += ' \\vspace{2mm}'
        latex_lines.append(line)
# -

# write pubs to file
with open('pubs.tex', 'w') as f:
    for l in latex_lines:
        f.write(l.replace('_', '\_') + '\n\n')


# ### load presentations and write to latex

# +
presentations = pd.read_csv('presentations.csv', index_col=0)
presentations = presentations.sort_values('year', ascending=False)

with open('presentations.tex', 'w') as f:
    for i in presentations.index:
        entry = presentations.loc[i,:]
        title = entry.title.strip('.')
        location = entry.location.strip('.')
        term = '\\vspace{2mm}'
        line = f'{entry.authors} ({entry.year}). {title}. {location}. {term} '
        f.write(line + '\n\n')

# +
# separately print colloquium talks
talks = pd.read_csv('talks.csv', index_col=0)
years = list(talks.year.unique())
years.sort()
years = years[::-1]

term = '\\vspace{2mm}'
lines = []
for y in years:
    talks_year = talks.query('year == %s' % y)
    lines.append('%s: %s' % (y, ','.join(list(talks_year.place))))

with open('talks.tex', 'w') as f:
    for l in lines:
        f.write(l + term + '\n\n')
# -




# +
# bespoke stuff

# +
# load original presentation list and clean up

with open('presentations_orig.txt') as f:
    pres_orig = [i.strip('\n') for i in f.readlines()]

presentations = []
ctr = 0
while ctr < len(pres_orig):
    # drop empty lines
    pres = pres_orig[ctr]
    if len(pres.replace(' ', '')) == 0:
        ctr+=1
        continue
        
    if pres.find('vspace') > -1:
        presentations.append(pres)
        ctr +=1
    else:
        tmp = pres
        for i in range(1, 10):
            ctr += 1
            tmp = tmp + ' ' + pres_orig[ctr]
            if tmp.find('vspace') > -1:
                ctr += 1
                break
        presentations.append(tmp)
# -

presentations_split = []
for p in presentations:
    p = p.replace('.org','').replace('?', '.')
    authors = p.split('(')[0].strip(' ').lstrip(' ').replace('.','').replace('\\&', '')
    date = p.split('(')[1].split(')')[0][:4]
    if p.find('textit{') > -1 and (p.find('Lecture') > -1 or p.find('resented') > -1):  # conference talks
        p_s = p.split('textit{')[1].split('}')
        title = p_s[0]
        location = p_s[1].split('\\vspace')[0].lstrip('.').lstrip(' ')
    elif p.find('resented') > -1: # posters
        p_s = [i.lstrip() for i in p.split(')')[1].lstrip('.').lstrip(' ').split('.')]
        title = p_s[0]
        location = p_s[1]
    else:
        p_s = [i.lstrip().replace('\\textit{','').replace('}', '').split('\\vspace')[0] for i in p.split(')')[1].lstrip('.').lstrip(' ').split('.')]
        title = p_s[0]
        location = p_s[1]
    presentations_split.append([authors, date, title, location])

pres_df = pd.DataFrame(presentations_split,
                       columns=['authors', 'year', 'title', 'location'])
pres_df.to_csv('presentations.csv')

# +
# add various links

osf_links = {29066077: 'https://osf.io/amxpv/',
             30061189: 'https://osf.io/z2gwf/',
             32043043: 'https://osf.io/fa6zr/',
             28053326: 'https://osf.io/spr9a/',
             32325057: 'https://osf.io/w6emk/',
             30842284: 'https://osf.io/5mjns/',
             31127115: 'https://osf.io/zk6w9/',
             28945803: 'https://osf.io/haf97/',
             30059542: 'https://osf.io/fdvrk/',
             29183655: 'https://osf.io/tgknp/',
             30001766: 'https://osf.io/t5kzx/'}

osf_df = pd.DataFrame(columns=['url'], index=list(osf_links.keys()))
for l in osf_links:
    osf_df.loc[l, 'url'] = osf_links[l]
    
osf_df.to_csv('osf_links.csv')


code_links = {31127115: 'https://github.com/IanEisenberg/Self_Regulation_Ontology',
              24981045: 'https://github.com/poldrack/rtmodel',
              26648521: 'https://github.com/poldrack/myconnectome',
              23071428: 'https://github.com/poldrack/LatentStructure'}

code_df = pd.DataFrame(columns=['url'], index=list(code_links.keys()))
for l in code_links:
    code_df.loc[l, 'url'] = code_links[l]
    
code_df.to_csv('code_links.csv')

# +
# invited talks

with open('invited_talks.txt') as f:
    lines = [i.strip() for i in f.readlines()]

talks_long = []
for l in lines:
    if len(l) == 0:
        continue
    year, talks = l.split(':')
    talks = talks.split('\\vspace')[0]

    for t in talks.split(';'):
        talks_long.append([year, t])
    
talks_df = pd.DataFrame(talks_long,columns=['year', 'place'])
talks_df.to_csv('talks.csv')
# -

l

year

