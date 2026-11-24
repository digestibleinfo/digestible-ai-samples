"""Our checker for the three ffmpeg-skill jobs. Usage: python check.py <jobN> <project_folder> <source_folder_with_truth.json> <out_json>
Needs faster-whisper + jiwer in its own venv. The agent's claims are never read."""
import json, re, subprocess, sys, hashlib, os
from pathlib import Path
import jiwer
P=Path(sys.argv[2]); SRC=Path(sys.argv[3]); OUT=Path(sys.argv[4]); job=sys.argv[1]
truth=json.load(open(SRC/"truth.json",encoding="utf-8")); sents=truth["sentences"]
norm=lambda s:" ".join(re.findall(r"[a-z0-9']+",s.lower()))
ref=norm(" ".join(s["text"] for s in sents))
def sh(*a): return subprocess.run(list(a),capture_output=True,text=True)
def probe(f):
    r=sh("ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,codec_name,width,height,duration","-of","json",str(f))
    return json.loads(r.stdout)
def silences(f,db=-35,d=0.5):
    r=sh("ffmpeg","-hide_banner","-nostats","-i",str(f),"-af",f"silencedetect=n={db}dB:d={d}","-f","null","-")
    st=[float(x) for x in re.findall(r"silence_start: ([\d.]+)",r.stderr)]
    en=[(float(a),float(b)) for a,b in re.findall(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)",r.stderr)]
    return [{"end":e,"dur":dd} for e,dd in en], r.stderr
def whisper(f):
    from faster_whisper import WhisperModel
    m=WhisperModel("small",device="cpu",compute_type="int8")
    seg,_=m.transcribe(str(f),language="en",word_timestamps=True)
    words=[]
    for s in seg:
        for w in s.words: words.append({"w":w.word,"s":w.start,"e":w.end})
    return words
def mean_vol(f):
    r=sh("ffmpeg","-hide_banner","-i",str(f),"-af","volumedetect","-f","null","-")
    m=re.search(r"mean_volume: (-?[\d.]+) dB",r.stderr); return float(m.group(1)) if m else None
res={"job":job,"checks":{}}; C=res["checks"]
def put(k,ok,**d): C[k]={"pass":bool(ok),**d}
src=P/"source.mp4"
if job=="job1":
    f=P/"cut.mp4"
    if not f.exists(): put("C1",False,why="cut.mp4 missing")
    else:
        pr=probe(f); types={s["codec_type"] for s in pr["streams"]}; dur=float(pr["format"]["duration"])
        put("C1",{"video","audio"}<=types and dur>0,duration=dur,streams=sorted(types))
        sil,_=silences(f); put("C2",len(sil)==0,left=sil,count=len(sil))
        w=whisper(f); hyp=norm(" ".join(x["w"] for x in w)); wer=jiwer.wer(ref,hyp)
        put("C3_wer",wer<=0.02,wer=round(wer,4),n_ref=len(ref.split()),n_hyp=len(hyp.split()))
        miss=[s["n"] for s in sents if norm(s["text"]).split()[0] not in hyp.split() or norm(s["text"]).split()[-1] not in hyp.split()]
        put("C3_edges",not miss,sentences_missing_first_or_last_word=miss)
        sdur=float(probe(src)["format"]["duration"]); sil_src,_=silences(src); tot=sum(x["dur"] for x in sil_src)
        removed=sdur-dur
        put("C4",removed<=tot+1.0 and dur>=sdur-tot-0.001,source_dur=sdur,source_silence_total=round(tot,2),n_source_silences=len(sil_src),removed=round(removed,2),cut_dur=dur)
        vs=[float(s.get("duration",0)) for s in pr["streams"] if s["codec_type"]=="video"]; as_=[float(s.get("duration",0)) for s in pr["streams"] if s["codec_type"]=="audio"]
        put("C5_durations",abs(vs[0]-as_[0])<=0.1 if vs and as_ else False,video=vs,audio=as_)
        # spot-check frames at the start of sentences 3, 7, 12 as found in the cut's transcript
        spots=[]
        for n in (3,7,12):
            first=norm(sents[n-1]["text"]).split()[0]; prev=norm(sents[n-2]["text"]).split()[-1]
            t=next((x["s"] for i,x in enumerate(w) if norm(x["w"])==first and i>0 and norm(w[i-1]["w"])==prev),None)
            spots.append({"sentence":n,"t_in_cut":t})
        res["spot_times"]=spots
elif job=="job2":
    f=P/"captions.srt"
    if not f.exists(): put("C6",False,why="captions.srt missing")
    else:
        txt=f.read_text(encoding="utf-8",errors="replace")
        cues=[]
        for blk in re.split(r"\n\s*\n",txt.strip()):
            m=re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)\s*\n(.*)",blk,re.S)
            if m:
                g=[int(x) for x in m.groups()[:8]]
                cues.append({"s":g[0]*3600+g[1]*60+g[2]+g[3]/1000,"e":g[4]*3600+g[5]*60+g[6]+g[7]/1000,"t":m.group(9).strip()})
        order=all(cues[i]["e"]<=cues[i+1]["s"]+1e-6 and cues[i]["s"]<cues[i]["e"] for i in range(len(cues)-1)) if cues else False
        longc=[c for c in cues if c["e"]-c["s"]>7 or len(c["t"].split("\n"))>2]
        put("C6",bool(cues) and order and not longc,n_cues=len(cues),in_order_nonoverlap=order,cues_too_long_or_3plus_lines=len(longc))
        hyp=norm(" ".join(c["t"] for c in cues)); wer=jiwer.wer(ref,hyp)
        a=ref.split(); b=hyp.split()
        put("C7",wer<=0.10,wer=round(wer,4),n_ref=len(a),n_hyp=len(b))
        offs=[]
        for s in sents:
            c=next((c for c in cues if c["s"]-0.05<=s["start"]<=c["e"]+0.05 or (c["s"]>=s["start"]-0.3 and norm(c["t"]).split()[:1]==norm(s["text"]).split()[:1])),None)
            # cue containing the sentence start: pick cue whose text begins with the sentence's first words, closest in time
            first3=" ".join(norm(s["text"]).split()[:2])
            cand=[c for c in cues if norm(c["t"]).startswith(first3)]
            c=min(cand,key=lambda c:abs(c["s"]-s["start"])) if cand else None
            offs.append({"n":s["n"],"truth":s["start"],"cue_start":c["s"] if c else None,"offset":round(c["s"]-s["start"],3) if c else None})
        valid=[abs(o["offset"]) for o in offs if o["offset"] is not None]
        put("C8",len(valid)==len(sents) and max(valid)<=0.3,worst=max(valid) if valid else None,median=sorted(valid)[len(valid)//2] if valid else None,unmatched=[o["n"] for o in offs if o["offset"] is None],offsets=offs)
    sha=hashlib.sha256(src.read_bytes()).hexdigest(); orig=(SRC/"source.sha256").read_text().strip()
    put("C9",sha==orig,sha256=sha)
elif job=="job3":
    f=P/"short.mp4"
    if not f.exists(): put("C10",False,why="short.mp4 missing")
    else:
        pr=probe(f); v=[s for s in pr["streams"] if s["codec_type"]=="video"]; a=[s for s in pr["streams"] if s["codec_type"]=="audio"]
        dur=float(pr["format"]["duration"]); sd=float(probe(src)["format"]["duration"])
        ok=bool(v and a) and (v[0]["width"],v[0]["height"])==(1080,1920) and v[0]["codec_name"]=="h264" and abs(dur-(sd+2))<=0.3
        put("C10",ok,w=v[0]["width"] if v else None,h=v[0]["height"] if v else None,vcodec=v[0]["codec_name"] if v else None,has_audio=bool(a),duration=dur,source=sd,expected=sd+2)
        mv=mean_vol(f); ms=mean_vol(src)
        put("C13_volume",mv is not None and abs(mv-ms)<=3,short_mean_db=mv,source_mean_db=ms)
        sil,_=silences(f); ns=len(silences(src)[0]); put("C13_gaps",len(sil)<=ns,short_silences=len(sil),source_silences=ns,note="source has our own 6 inserted pauses; the criterion is no EXTRA gap at the join (fixed 2026-11-24 after first run: compared with the source count, not zero)")
json.dump(res,open(OUT,"w",encoding="utf-8"),indent=1); print(json.dumps({k:v["pass"] for k,v in C.items()}))
