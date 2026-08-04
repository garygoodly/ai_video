from __future__ import annotations
import re
from collections import defaultdict
from finance_video_factory.models import Article, RankedEvent

KEYWORDS={"fed":18,"federal reserve":18,"cpi":17,"inflation":15,"jobs":14,"payroll":16,"rate":10,"treasury":10,"earnings":8,"tariff":13,"oil":10,"bitcoin":9,"recession":15,"gdp":15,"sec":8,"bank":8,"crash":18,"record":7}

class EventRanker:
    def rank(self, articles: list[Article], top_n: int) -> list[RankedEvent]:
        groups=defaultdict(list)
        for i,a in enumerate(articles):
            tokens=[w for w in re.findall(r"[a-zA-Z]{4,}",a.title.lower()) if w not in {"with","from","that","this","after","into","over","amid","says"}]
            key=" ".join(tokens[:4]) or a.title.lower()
            groups[key].append(i)
        events=[]
        for key,indexes in groups.items():
            text=" ".join(articles[i].title.lower()+" "+articles[i].summary.lower() for i in indexes)
            score=20+min(len(indexes)*8,24)+sum(v for k,v in KEYWORDS.items() if k in text)
            sources=len({articles[i].source for i in indexes})
            score+=min(sources*6,18)
            events.append(RankedEvent(title=articles[indexes[0]].title,score=score,article_indexes=indexes,reason=f"{len(indexes)} article(s), {sources} source(s), macro/market keyword weighting"))
        return sorted(events,key=lambda x:x.score,reverse=True)[:top_n]
