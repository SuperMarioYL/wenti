import json
from wenti.packs import load_pack
from wenti.scorer.score import score_draft
text='清晨，菜市场的灯还亮着。老周把白菜码在摊位上，水汽从叶脉间慢慢散开。\n\n街道醒了。\n\n他为什么还留在这里？女儿的信压在棋盘下面，时间在纸角留下浅浅的褶皱。'
r=score_draft(text,load_pack('sanlian'),dry_run=True)
print(json.dumps({'input':text,'pack':r.pack,'dry_run':r.dry_run,'sub_scores':r.sub_scores,'total':r.total},ensure_ascii=False,indent=2))
