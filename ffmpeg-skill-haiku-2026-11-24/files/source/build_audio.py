import json, numpy as np, soundfile as sf, sys
from pathlib import Path
J=Path(sys.argv[1]); V=J/"source/voicejob/voice"
d=json.load(open(V/"durations.json",encoding="utf-8"))
pauses={2:1.0,4:1.2,6:1.5,8:1.5,10:2.0,12:2.0}   # after sentence n
nat=0.35
out=[];t=0.0;truth=[];sr=None
for i,s in enumerate(d,1):
    x,sr=sf.read(V/s["file"]); 
    if x.ndim>1:x=x.mean(1)
    out.append(x); truth.append({"n":i,"start":round(t,3),"end":round(t+len(x)/sr,3),"text":s["text"].lstrip("\ufeff")}); t+=len(x)/sr
    if i<len(d):
        g=pauses.get(i,nat); out.append(np.zeros(int(g*sr))); t+=g
a=np.concatenate(out); sf.write(J/"source/audio.wav",a,sr)
json.dump({"sentences":truth,"inserted_pauses":[{"after_sentence":k,"seconds":v} for k,v in pauses.items()],"natural_gap_s":nat,"total_s":round(t,3)},open(J/"source/truth.json","w"),indent=1)
print(round(t,2))
