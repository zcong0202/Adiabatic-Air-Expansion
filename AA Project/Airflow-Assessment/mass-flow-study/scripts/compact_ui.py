"""Compact presentation. Keep detailed evidence in disclosure panels."""
from lxml import html,etree

def disclosure(title,nodes,cls='compact-details'):
    d=html.Element('details',{'class':cls});s=html.Element('summary');s.text=title;d.append(s)
    for n in nodes:d.append(n)
    return d

def compact_section(markup,kind):
    root=html.fromstring(markup)
    if kind=='components':
        heading=root.find('.//h2');heading.text='Components'
        for n in root.xpath('./div[contains(@class,"section-head")]//p[contains(@class,"eyebrow")]'):n.getparent().remove(n)
        header=root[0];filters=root.xpath('./div[contains(@class,"catalogue-controls")]')[0];table=root.xpath('./div[contains(@class,"table")]')[0]
        calculator=root.xpath('./div[contains(@class,"plant-calculator")]')[0]
        for row in table.xpath('.//tr[@data-component]'):
            cell=row[2];detail=cell.find('details');intro=cell.find('p')
            if intro is not None and detail is not None:detail.insert(1,intro)
            if detail is not None:detail.find('summary').text='Specs / fit'
        remaining=[n for n in list(root) if n not in [header,filters,table,calculator]]
        for n in list(root):root.remove(n)
        root.append(header);p=html.Element('p',{'class':'compact-context'});p.text='4 loaded motors · 77.6 g/s nominal · source and fittings unverified';root.append(p)
        root.extend([filters,table,disclosure('Sizing calculator',[calculator]),disclosure('System layout, assumptions and next steps',remaining)])
    elif kind=='nozzles':
        root.find('.//h2').text='Nozzles'
        for n in root.xpath('./div[contains(@class,"section-head")]//p[contains(@class,"eyebrow")]'):n.getparent().remove(n)
        notes=root.xpath('./p');detail=disclosure('Fit and CFD conditions',notes)
        root.insert(1,detail)
        p=html.Element('p',{'class':'compact-context'});p.text='23 designs · STL mm / STEP m · printed fit unverified';root.insert(1,p)
        for card in root.xpath('.//article[@data-nozzle]'):
            content=card.xpath('./div[contains(@class,"nozzle-content")]')[0]
            note=content.find('p');note.text={'current':'Unfitted hose interface','early':'Concept · CFD unaccepted','cone':'Prototype · fit unverified'}[card.get('data-group')]
            description=content.xpath('./p')[1];mount=content.xpath('./p')[2]
            limits=content.xpath('./details[contains(@class,"nozzle-limits")]')[0];limits.find('summary').text='Dimensions / fit / evidence';limits.insert(1,description);limits.insert(2,mount)
            links=content.xpath('./div[contains(@class,"links")]')[0]
            extra=list(links)[2:]
            if extra:content.insert(list(content).index(links)+1,disclosure('More files',extra))
            evidence=content.xpath('./details[contains(@class,"nozzle-evidence")]')[0];evidence.attrib.pop('open',None)
            evidence.find('summary').text=evidence.find('summary').text.replace('CFD at 20 and 50 cm','20 / 50 cm CFD')
            deltas=evidence.xpath('./div[contains(@class,"nozzle-deltas")]')
            if deltas:content.insert(list(content).index(evidence),deltas[0])
    return etree.tostring(root,encoding='unicode',method='html')
