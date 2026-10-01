"""Rebuild the verified 2024–2026 supplement, leaving every original clue intact."""
import csv
import hashlib
import json
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'
SOURCES={
 'rm26':'https://www.realmadrid.com/en-US/news/football/first-team/latest-news/debut-en-partido-oficial-de-los-seis-nuevos-fichajes-del-real-madrid-22-08-2026',
 'rodri26':'https://www.fcbarcelona.com/en/football/first-team/news/4561501/fc-barcelona-sign-rodrigo-hernandez',
 'robertson26':'https://www.liverpoolfc.com/news/andy-robertson-join-tottenham-hotspur',
 'city26':'https://www.mancity.com/news/mens/enzo-fernandez-squad-number-revealed-63923952',
 'enzo26':'https://www.mancity.com/news/mens/enzo-fernandez-signs-for-city-63923893',
 'barcola26':'https://www.liverpoolfc.com/news/liverpool-sign-bradley-barcola-paris-saint-germain',
 'araujo26':'https://www.liverpoolfc.com/news/liverpool-agree-deal-sign-ronald-araujo-loan',
 'wc26':'https://inside.fifa.com/organisation/news/spain-crowned-world-cup-2026-champions-new-york-new-jersey',
 'ucl26':'https://www.uefa.com/uefachampionsleague/news/02a5-20c02e59f219-15e92acdc717-1000--paris-retain-champions-league-holders-edge-arsenal-on-pena/',
 'psg26':'https://www.uefa.com/uefachampionsleague/news/02a5-20901454177c-738c0ac757df-1000--champions-league-final-meet-the-teams/',
 'villa26':'https://www.uefa.com/uefaeuropaleague/match/2047743--freiburg-vs-aston-villa/',
 'villa26title':'https://www.uefa.com/uefaeuropaleague/news/02a1-1fce257db598-8d600e9b2af4-1000--2025-26-europa-league-meet-the-winners/',
 'ucl25':'https://www.uefa.com/uefachampionsleague/news/0299-1de417608530-15b01ff7b150-1000--paris-win-champions-league-doue-double-helps-secure-reco/',
 'cwc25':'https://www.chelseafc.com/en/match/chelsea-vs-paris-saintgermain-fifa-club-world-cup-2025-07-13',
 'cwc25awards':'https://inside.fifa.com/official-documents/annual-report/2025/fifa-club-world-cup-2025/summary',
 'wirtz25':'https://www.liverpoolfc.com/news/liverpool-agree-signing-florian-wirtz-bayer-leverkusen',
 'isak25':'https://www.liverpoolfc.com/news/liverpool-complete-signing-alexander-isak',
 'trent25':'https://www.realmadrid.com/en-US/news/football/first-team/latest-news/alexander-arnold-firmo-su-contrato-con-el-real-madrid-12-06-2025',
 'diaz25':'https://fcbayern.com/en/news/2025/07/fc-bayern-sign-luis-diaz-from-liverpool',
 'gyokeres25':'https://www.arsenal.com/gallery/gallery-viktor-gyokeres-signs-aJwUR1w3gKni',
 'donnarumma25':'https://www.premierleague.com/en/news/4373807/man-city-sign-goalkeeper-donnarumma-from-psg',
 'ederson25':'https://www.mancity.com/news/mens/ederson-leaves-manchester-city-fenerbahce-transfer-63892390',
 'kdb25':'https://sscnapoli.it/en/sscn-ufficiale-lingaggio-di-de-bruyne/',
 'felix25':'https://www.chelseafc.com/en/news/article/joao-felix-completes-al-nassr-move',
 'ballon25':'https://www.uefa.com/ballondor/video/029d-1ec96db52039-479f624d5b84-1000--ousmane-dembele-wins-2025-ballon-d-or/',
 'euro24':'https://www.uefa.com/uefaeuro/history/news/028f-1b61cc9835db-185592165f27-1000--uefa-euro-2024-at-a-glance/',
 'euro24final':'https://www.uefa.com/uefaeuro/history/news/028f-1b5e5c2b7b67-d5faab9be20b-1000--spain-2-1-england-late-oyarzabal-winner-earns-la-roya-reco/',
 'ucl24':'https://www.uefa.com/uefachampionsleague/news/028e-1b07e18d875a-ba78e4b9d9fc-1000--real-madrid-win-champions-league-carvajal-and-vinicius-junior-see-off-dortmund/',
}

def main():
    banks={m:json.loads((DATA/f'{m}.json').read_text()) for m in ('players','clubs')}
    lookup={m:{x['answer']:x for x in rows} for m,rows in banks.items()}
    # Idempotent: replace only this supplement's entries; retain custom additions.
    for rows in banks.values():
        for x in rows:
            x['extra_clues']=[c for c in x.get('extra_clues',[]) if c.get('supplement')!='verified_2026_v2']
    added=[]
    def add(name,tier,year,text,source,mode='players',kind='event'):
        item=lookup[mode][name]
        clue={'text':text,'difficulty':tier,'event_year':year,'kind':kind,
              'source_url':SOURCES[source],'checked_on':'2026-10-01',
              'supplement':'verified_2026_v2'}
        item['extra_clues'].append(clue)
        added.append((mode,item,clue))
    def club(name,tier,year,text,source):add(name,tier,year,text,source,'clubs')

    # 2026 transfers: dated facts, without overwriting historic club clues.
    for name in ('Bernardo Silva','Denzel Dumfries','Cucurella'):
        add(name,2,2026,'كنت ضمن ستة وافدين جدد ظهروا رسمياً لريال مدريد ضد إسبانيول في أغسطس ٢٠٢٦.','rm26',kind='transfer')
    add('Bernardo Silva',4,2026,'ظهرت مع ريال مدريد في أغسطس ٢٠٢٦؛ اسمي الأول برناردو.','rm26',kind='transfer')
    add('Denzel Dumfries',4,2026,'كنت من صفقات ريال مدريد التي ظهرت في أغسطس ٢٠٢٦؛ اسمي الأول دينزل.','rm26',kind='transfer')
    add('Cucurella',4,2026,'ظهرت رسمياً بقميص ريال مدريد في أغسطس ٢٠٢٦؛ اسم عائلتي يبدأ بـ كوك.','rm26',kind='transfer')
    add('Rodri',2,2026,'في أغسطس ٢٠٢٦ وقّعت لنادٍ كتالوني حتى يونيو ٢٠٣٠.','rodri26',kind='transfer')
    add('Rodri',4,2026,'انتقلت من مانشستر سيتي إلى برشلونة في أغسطس ٢٠٢٦؛ ألعب في الارتكاز.','rodri26',kind='transfer')
    add('Andrew Robertson',2,2026,'أُعلن في يونيو ٢٠٢٦ اتفاق انتقالي لنادٍ لندني بعد تسع سنوات في ليفربول.','robertson26',kind='transfer')
    add('Andrew Robertson',4,2026,'اتفقت على الانضمام لتوتنهام في يوليو ٢٠٢٦؛ ظهير اسكتلندي واسمي أندرو.','robertson26',kind='transfer')
    add('Gerónimo Rulli',3,2026,'كنت ضمن الحراس الذين انضموا لمانشستر سيتي في صيف ٢٠٢٦؛ اسمي الأول جيرونيمو.','city26',kind='transfer')
    club('Real Madrid',2,2026,'قدّمت ستة وافدين جدد رسمياً ضد إسبانيول في أغسطس ٢٠٢٦، بينهم برناردو ودومفريس.','rm26')
    club('Barcelona',2,2026,'أعلنت ضم رودري من مانشستر سيتي في أغسطس ٢٠٢٦ بعقد حتى ٢٠٣٠.','rodri26')
    club('Tottenham Hotspur',2,2026,'اتفقت على ضم أندرو روبرتسون بعد نهاية عقده مع ليفربول في صيف ٢٠٢٦.','robertson26')
    club('Manchester City',2,2026,'تعاقدت مع إنزو فرنانديز من تشيلسي في سبتمبر ٢٠٢٦ لخمس سنوات.','enzo26')
    club('Manchester City',3,2026,'حصل إنزو فرنانديز عند انضمامه لي سنة ٢٠٢٦ على الرقم ١٧ الذي اشتهر به دي بروين.','city26')
    club('Liverpool',2,2026,'أعلنت ضم برادلي باركولا من باريس سان جيرمان في أغسطس ٢٠٢٦.','barcola26')
    club('Liverpool',3,2026,'أعلنت اتفاق إعارة رونالد أراوخو من برشلونة لموسم ٢٠٢٦–٢٠٢٧، مشروطاً بالتصاريح والموافقة الدولية.','araujo26')
    club('Chelsea',2,2026,'غادرني إنزو فرنانديز إلى مانشستر سيتي في سبتمبر ٢٠٢٦.','enzo26')

    # 2026 World Cup: FIFA's final/awards report, not forecasts.
    add('Ferran Torres',1,2026,'حسمت نهائي كأس العالم ٢٠٢٦ بهدف في الدقيقة ١٠٦.','wc26')
    add('Ferran Torres',3,2026,'سجّلت هدف إسبانيا الوحيد ضد الأرجنتين في نهائي مونديال ٢٠٢٦.','wc26')
    add('Rodri',1,2026,'فزت بالكرة الذهبية لأفضل لاعب في كأس العالم ٢٠٢٦.','wc26')
    add('Unai Simón',1,2026,'نلت القفاز الذهبي في كأس العالم ٢٠٢٦.','wc26')
    add('Unai Simón',3,2026,'حارس إسباني حصل على جائزة أفضل حارس في مونديال ٢٠٢٦.','wc26')

    # 2026 UCL: short factual clues, grouped to avoid excessive source reuse.
    for name in ('Achraf Hakimi','Marquinhos','Nuno Mendes','Fabián','Ousmane Dembélé','Khvicha Kvaratskhelia'):
        add(name,2,2026,'لعبت أساسياً لباريس في نهائي دوري الأبطال ٢٠٢٦.','ucl26')
    for name in ('William Saliba','Gabriel','Declan Rice','Bukayo Saka','Martin Ødegaard','Kai Havertz'):
        add(name,2,2026,'بدأت مع آرسنال نهائي دوري الأبطال ٢٠٢٦.','ucl26')
    add('Gonçalo Ramos',2,2026,'دخلت بديلاً لديمبيلي بنهائي دوري الأبطال ٢٠٢٦.','ucl26')
    add('Ousmane Dembélé',3,2026,'سجّلت تعادل باريس من ركلة جزاء بنهائي دوري الأبطال ٢٠٢٦.','ucl26')
    add('Kai Havertz',1,2026,'سجّلت في نهائي أوروبا لتشيلسي ٢٠٢١ وآرسنال ٢٠٢٦.','ucl26')
    add('Khvicha Kvaratskhelia',1,2026,'حصلت على ركلة جزاء أعادت باريس للمباراة بنهائي دوري الأبطال ٢٠٢٦.','ucl26')
    add('Nuno Mendes',1,2026,'تصدى رايا لركلتي الترجيحية بنهائي دوري الأبطال ٢٠٢٦.','ucl26')
    club('Paris Saint-Germain',1,2026,'حافظت على لقب دوري الأبطال سنة ٢٠٢٦ بعد النهائي في بودابست.','psg26')
    club('Paris Saint-Germain',3,2026,'هزمت آرسنال بترجيح ٤–٣ بعد تعادل ١–١ بنهائي دوري الأبطال ٢٠٢٦.','psg26')
    club('Arsenal',2,2026,'خسرت نهائي دوري الأبطال ٢٠٢٦ أمام باريس بركلات الترجيح بعد تعادل ١–١.','psg26')
    club('Bayern Munich',1,2026,'ودّعت دوري الأبطال ٢٠٢٦ أمام باريس بنصف النهائي بمجموع ٦–٥.','psg26')
    club('Liverpool',1,2026,'خرجت من ربع نهائي دوري الأبطال ٢٠٢٦ أمام باريس بمجموع ٤–٠.','psg26')
    club('Chelsea',1,2026,'خسرت أمام باريس في ثمن نهائي دوري الأبطال ٢٠٢٦ بمجموع ٨–٢.','psg26')

    # 2026 Europa League finalists: keep role-specific facts separate from names.
    for name in ('Damián Martínez','Victor Lindelöf','Youri Tielemans','Lucas Digne','Pau Torres','Emiliano Buendía'):
        add(name,2,2026,'بدأت أساسياً لأستون فيلا بنهائي الدوري الأوروبي ٢٠٢٦.','villa26')
    add('Jadon Sancho',2,2026,'دخلت لأستون فيلا بديلاً لبوينديا بنهائي الدوري الأوروبي ٢٠٢٦.','villa26')
    club('Aston Villa',1,2026,'توجت بالدوري الأوروبي ٢٠٢٦؛ أول لقب قاري لي منذ ١٩٨٢.','villa26title')
    club('Aston Villa',3,2026,'هزمت فرايبورغ ٣–٠ بنهائي الدوري الأوروبي ٢٠٢٦ في إسطنبول.','villa26')

    # Important 2025 transfer stories, with easier alternatives in slot 4.
    transfers=[
      ('Florian Wirtz','ليفركوزن','ليفربول','wirtz25'),
      ('Alexander Isak','نيوكاسل','ليفربول','isak25'),
      ('Trent Alexander-Arnold','ليفربول','ريال مدريد','trent25'),
      ('Luis Díaz','ليفربول','بايرن ميونخ','diaz25'),
      ('Viktor Gyökeres','سبورتينغ لشبونة','آرسنال','gyokeres25'),
      ('Gianluigi Donnarumma','باريس سان جيرمان','مانشستر سيتي','donnarumma25'),
      ('Ederson','مانشستر سيتي','فنربخشة','ederson25'),
      ('Kevin De Bruyne','مانشستر سيتي','نابولي','kdb25'),
      ('João Félix','تشيلسي','النصر السعودي','felix25'),
    ]
    for name,old,new,source in transfers:
        add(name,3,2025,f'انتقلت من {old} إلى {new} سنة ٢٠٢٥.',source,kind='transfer')
    add('Alexander Isak',1,2025,'قبل انتقالي في ٢٠٢٥، سجّلت ٦٢ هدفاً في ١٠٩ مباريات لنيوكاسل.','isak25')
    add('Luis Díaz',4,2025,'انضممت إلى بايرن في يوليو ٢٠٢٥ بالرقم ١٤؛ جناح كولومبي واسمي لويس.','diaz25')
    add('Florian Wirtz',2,2025,'انتقلت سنة ٢٠٢٥ إلى النادي نفسه الذي سبقني إليه زميلي فريمبونغ.','wirtz25')
    add('Jeremie Frimpong',3,2025,'انتقلت لليفربول في صيف ٢٠٢٥ قبل وصول زميلي فلوريان فيرتز.','wirtz25',kind='transfer')
    club('Liverpool',1,2025,'ضممت ألكسندر إيزاك من نيوكاسل في سبتمبر ٢٠٢٥ ليحمل الرقم ٩.','isak25')
    club('Bayer Leverkusen',2,2025,'غادرني فلوريان فيرتز إلى ليفربول في يونيو ٢٠٢٥.','wirtz25')
    club('Bayern Munich',2,2025,'تعاقدت مع لويس دياز من ليفربول سنة ٢٠٢٥ ومنحته الرقم ١٤.','diaz25')
    club('Manchester City',2,2025,'ضممت دوناروما من باريس في سبتمبر ٢٠٢٥ عقب رحيل إيدرسون.','donnarumma25')
    club('Fenerbahçe',2,2025,'تعاقدت مع الحارس البرازيلي إيدرسون من مانشستر سيتي سنة ٢٠٢٥.','ederson25')
    club('Napoli',2,2025,'انضم لي كيفن دي بروين سنة ٢٠٢٥ بعد عشر سنوات في مانشستر سيتي.','kdb25')
    club('Al Nassr',2,2025,'ضممت جواو فيليكس من تشيلسي بعقد دائم في يوليو ٢٠٢٥.','felix25')
    club('Arsenal',1,2025,'وقّعت مع المهاجم السويدي غيوكيريس من سبورتينغ لشبونة في يوليو ٢٠٢٥.','gyokeres25')

    # 2025 finals and awards.
    add('Ousmane Dembélé',1,2025,'فزت بالكرة الذهبية سنة ٢٠٢٥.','ballon25')
    add('Cole Palmer',1,2025,'حصلت على الكرة الذهبية لكأس العالم للأندية ٢٠٢٥.','cwc25awards')
    add('Cole Palmer',3,2025,'قدت تشيلسي للفوز على باريس ٣–٠ بنهائي مونديال الأندية ٢٠٢٥.','cwc25')
    club('Chelsea',1,2025,'فزت بكأس العالم للأندية الموسّع سنة ٢٠٢٥.','cwc25')
    club('Chelsea',3,2025,'هزمت باريس ٣–٠ بنهائي مونديال الأندية ٢٠٢٥ بفضل تألق بالمر.','cwc25')
    add('Achraf Hakimi',1,2025,'أصبحت أول مغربي يسجّل في نهائي كأس أوروبا سنة ٢٠٢٥.','ucl25')
    add('Khvicha Kvaratskhelia',3,2025,'سجّلت لباريس ضد إنتر بنهائي دوري الأبطال ٢٠٢٥.','ucl25')
    add('Gianluigi Donnarumma',2,2025,'حافظت على نظافة شباكي بنهائي دوري الأبطال ٢٠٢٥.','ucl25')
    add('Ousmane Dembélé',2,2025,'صنعت هدفين لباريس بنهائي دوري الأبطال ٢٠٢٥.','ucl25')
    for name in ('Lautaro Martínez','Nicolò Barella','Marcus Thuram','Yann Sommer','Benjamin Pavard','Alessandro Bastoni','Denzel Dumfries','Henrikh Mkhitaryan','Hakan Çalhanoğlu'):
        add(name,2,2025,'بدأت لإنتر نهائي دوري الأبطال ٢٠٢٥ الذي انتهى ٠–٥.','ucl25')
    club('Paris Saint-Germain',2,2025,'حققت أول دوري أبطال في تاريخي سنة ٢٠٢٥ بفوز ٥–٠.','ucl25')
    club('Inter Milan',1,2025,'خسرت نهائي دوري الأبطال ٢٠٢٥ في ميونخ بخمسة أهداف دون رد.','ucl25')
    club('Tottenham Hotspur',1,2025,'تأهلت للسوبر الأوروبي ٢٠٢٥ بصفتي بطل الدوري الأوروبي.','ucl25')

    # 2024 tournament records make earlier hints more interesting too.
    euro=[
      ('Rodri',1,'كنت أفضل لاعب في يورو ٢٠٢٤.'),
      ('Lamine Yamal',1,'نلت جائزة أفضل لاعب شاب في يورو ٢٠٢٤.'),
      ('Lamine Yamal',2,'صنعت أربعة أهداف في يورو ٢٠٢٤، أكثر من أي لاعب.'),
      ('Cody Gakpo',1,'تقاسمت صدارة هدافي يورو ٢٠٢٤ بثلاثة أهداف.'),
      ('Harry Kane',1,'تقاسمت صدارة هدافي يورو ٢٠٢٤ بثلاثة أهداف.'),
      ('Jamal Musiala',1,'كنت من هدافي يورو ٢٠٢٤ بثلاثة أهداف.'),
      ('Dani Olmo',1,'تقاسمت لقب هداف يورو ٢٠٢٤ بثلاثة أهداف.'),
      ('Mike Maignan',1,'حققت أربع مباريات بشباك نظيفة في يورو ٢٠٢٤.'),
      ('Kylian Mbappé',1,'بلغت سرعتي المسجلة في يورو ٢٠٢٤ نحو ٣٦٫٥ كم/ساعة.'),
      ('Declan Rice',1,'قطعت نحو ٨٥٫٧ كيلومتراً في يورو ٢٠٢٤.'),
      ('Jude Bellingham',1,'نجحت في ٢٤ افتكاكاً للكرة في يورو ٢٠٢٤.'),
      ('Jérémy Doku',1,'سجّلت ٣٤ مراوغة ناجحة في يورو ٢٠٢٤.'),
      ('John Stones',1,'أكملت ٥٢٦ تمريرة في يورو ٢٠٢٤.'),
      ('Cristiano Ronaldo',1,'صارت يورو ٢٠٢٤ سادس مشاركة لي بنهائيات البطولة.'),
      ('Pepe',1,'لعبت في يورو ٢٠٢٤ بعمر ٤١ سنة، الأكبر بتاريخ البطولة.'),
      ('Luka Modrić',1,'صرت أكبر مسجّل بتاريخ اليورو بهدف ضد إيطاليا سنة ٢٠٢٤.'),
    ]
    for name,tier,text in euro:add(name,tier,2024,text,'euro24')
    add('Oyarzabal',1,2024,'سجّلت هدف الفوز قبل النهاية بأربع دقائق بنهائي يورو ٢٠٢٤.','euro24final')
    add('Oyarzabal',3,2024,'حسم هدفي فوز إسبانيا ٢–١ على إنكلترا بنهائي يورو ٢٠٢٤.','euro24final')
    add('Carvajal',1,2024,'فتحت التسجيل برأسية من ركنية في نهائي دوري الأبطال ٢٠٢٤.','ucl24')
    add('Vinícius Júnior',2,2024,'سجّلت الهدف الثاني ضد دورتموند بنهائي دوري الأبطال ٢٠٢٤.','ucl24')
    add('Toni Kroos',1,2024,'من ركنيتي جاء الهدف الأول بنهائي دوري الأبطال ٢٠٢٤.','ucl24')
    club('Real Madrid',1,2024,'حققت لقبي الأوروبي الخامس عشر سنة ٢٠٢٤.','ucl24')
    club('Borussia Dortmund',2,2024,'وصلت نهائي دوري الأبطال ٢٠٢٤ وخسرت ٠–٢ أمام ريال مدريد.','ucl24')

    for mode,rows in banks.items():
        (DATA/f'{mode}.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    with (DATA/'modern_clues.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f)
        w.writerow(['mode','item_id','answer','difficulty_1_hard_4_easy','event_year','kind','clue','source_url','checked_on'])
        for mode,item,c in added:
            w.writerow([mode,item['id'],item['answer'],c['difficulty'],c['event_year'],c['kind'],c['text'],c['source_url'],c['checked_on']])
    with (DATA/'modern_sources.json').open('w') as f:json.dump(SOURCES,f,indent=2)
    manifest=json.loads((DATA/'manifest.json').read_text())
    manifest.update(scope='Original historical bank plus selectively verified 2024–2026 events; original 2021 club clues remain dated.',version='2.0',checked_through='2026-10-01',topics_supported=True,
        modern_clues=len(added),modern_by_year=dict(Counter(str(c['event_year']) for _,_,c in added)),
        players_with_modern_clues=sum(bool(x['extra_clues']) for x in banks['players']),
        clubs_with_modern_clues=sum(bool(x['extra_clues']) for x in banks['clubs']))
    manifest['sha256']={f'{m}.json':hashlib.sha256((DATA/f'{m}.json').read_bytes()).hexdigest() for m in banks}
    (DATA/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    counts=defaultdict(int)
    for _,_,c in added:counts[c['source_url']]+=len(c['text'].split())
    assert max(counts.values())<=200,counts
    print(json.dumps({k:manifest[k] for k in ['modern_clues','modern_by_year','players_with_modern_clues','clubs_with_modern_clues']},ensure_ascii=False))


if __name__=='__main__':main()
