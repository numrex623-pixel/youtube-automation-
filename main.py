
import os, json, math, asyncio, subprocess
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from groq import Groq
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT=Path(__file__).parent
OUT=ROOT/"output"; TEMP=ROOT/"assets"/"temp"; CHARS=ROOT/"characters"
W,H,FPS=720,1280,24
MODEL=os.getenv("GROQ_MODEL","openai/gpt-oss-120b")
OUT.mkdir(exist_ok=True); TEMP.mkdir(parents=True,exist_ok=True)
CAST={
 "Rocky":{"file":"rocky_potato.png","voice":"ur-PK-AsadNeural","color":(46,105,190),"mouth":(0.50,0.37)},
 "Brock":{"file":"brock_broccoli.png","voice":"ur-PK-AsadNeural","color":(38,126,75),"mouth":(0.51,0.48)},
 "Caro":{"file":"caro_carrot.png","voice":"ur-PK-UzmaNeural","color":(229,126,54),"mouth":(0.50,0.46)},
 "Tommy":{"file":"tommy_tomato.png","voice":"ur-PK-AsadNeural","color":(190,58,57),"mouth":(0.50,0.43)}
}
def run(cmd):
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if p.returncode: raise RuntimeError(p.stderr[-4000:])
 return p
def ai_story():
 key=os.getenv("GROQ_API_KEY")
 if not key: raise RuntimeError("Missing GROQ_API_KEY secret.")
 prompt=("Write one original, family-friendly Pakistani Urdu comedy story for YouTube Shorts. "
 "Use Urdu script, not Roman Urdu. Four scenes exactly. Use only Rocky (overconfident potato), "
 "Brock (sensible broccoli), Caro (clever carrot), Tommy (dramatic tomato). A funny hook, "
 "escalating misunderstanding and punchline. No history, facts, politics or adult jokes. "
 "Return JSON only: {\"topic\":\"English topic\",\"title\":\"Urdu title\","
 "\"scenes\":[{\"speaker\":\"Rocky\",\"line\":\"Urdu dialogue\",\"action\":\"short English visual direction\"},"
 "{\"speaker\":\"Brock\",\"line\":\"...\",\"action\":\"...\"},"
 "{\"speaker\":\"Caro\",\"line\":\"...\",\"action\":\"...\"},"
 "{\"speaker\":\"Tommy\",\"line\":\"...\",\"action\":\"...\"}],"
 "\"hashtags\":[\"#Shorts\",\"#UrduComedy\"]}. Keep each line short.")
 client=Groq(api_key=key,timeout=90,max_retries=2)
 error=None
 for _ in range(3):
  try:
   r=client.chat.completions.create(model=MODEL,messages=[
    {"role":"system","content":"Write funny clean Pakistani Urdu cartoon dialogue. Return valid JSON only."},
    {"role":"user","content":prompt}],temperature=0.85,max_completion_tokens=1800,
    response_format={"type":"json_object"})
   data=json.loads(r.choices[0].message.content or "")
   if len(data.get("scenes",[]))!=4: raise ValueError("Story must contain four scenes.")
   for s in data["scenes"]:
    if s.get("speaker") not in CAST or not s.get("line"): raise ValueError("Invalid scene speaker or dialogue.")
   data["hashtags"]=[str(x) for x in data.get("hashtags",[])[:5]]
   return data
  except Exception as e: error=e
 raise RuntimeError(f"Groq story generation failed: {error}")
async def make_voice(text,voice,path):
 await edge_tts.Communicate(text=text,voice=voice,rate="+5%").save(str(path))
def get_font(size):
 for p in ["/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
  if Path(p).exists(): return ImageFont.truetype(p,size)
 return ImageFont.load_default()
def make_frame(frame_no,elapsed,speaker,title):
 from PIL import ImageFilter
 img=Image.new("RGB",(W,H),(25,43,69)); d=ImageDraw.Draw(img)
 for y in range(H):
  v=int(26+32*y/H); d.line((0,y,W,y),fill=(v,v+12,min(125,v+42)))
 d.ellipse((45,180,675,850),fill=(39,64,91))
 d.ellipse((-80,940,800,1400),fill=(30,44,60))
 d.rounded_rectangle((35,48,685,142),radius=24,fill=(246,248,250))
 d.text((W//2,95),title[:34],font=get_font(26),fill=(26,40,58),anchor="mm")
 cfg=CAST[speaker]; path=CHARS/cfg["file"]
 sprite=Image.open(path).convert("RGBA")
 scale=min(570/sprite.width,790/sprite.height)*(1+0.012*math.sin(elapsed*5))
 nw,nh=int(sprite.width*scale),int(sprite.height*scale)
 sprite=sprite.resize((nw,nh),Image.Resampling.LANCZOS)
 bob=abs(math.sin(elapsed*4.5))*15; sway=math.sin(elapsed*2.5)*7
 x=int((W-nw)/2+sway); y=int(270-bob)
 shadow=Image.new("RGBA",(W,H),(0,0,0,0)); sd=ImageDraw.Draw(shadow)
 sd.ellipse((145,1080,575,1170),fill=(0,0,0,100))
 shadow=shadow.filter(ImageFilter.GaussianBlur(22))
 canvas=Image.alpha_composite(img.convert("RGBA"),shadow)
 canvas.alpha_composite(sprite,(x,y))
 # Animated speaking indicator; no subtitles or dialogue text.
 if frame_no%8<5:
  md=ImageDraw.Draw(canvas); mx=x+int(nw*cfg["mouth"][0]); my=y+int(nh*cfg["mouth"][1])
  md.ellipse((mx-9,my-5,mx+9,my+8),fill=(64,18,24,225))
 return canvas.convert("RGB")
def render(story,audios,stem):
 durations=[]
 for p in audios:
  q=run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(p)])
  durations.append(max(3.5,float(q.stdout.strip())))
 frame_dir=TEMP/"frames"; frame_dir.mkdir(exist_ok=True)
 for p in frame_dir.glob("*.jpg"): p.unlink()
 n=0
 for i,scene in enumerate(story["scenes"]):
  count=round(durations[i]*FPS)
  for j in range(count):
   make_frame(j,j/FPS,scene["speaker"],story.get("title","مزاحیہ سبزیوں کی کہانی")).save(frame_dir/f"{n:06d}.jpg",quality=88)
   n+=1
 silent=TEMP/"silent.mp4"
 run(["ffmpeg","-y","-framerate",str(FPS),"-i",str(frame_dir/"%06d.jpg"),"-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p",str(silent)])
 listing=TEMP/"audio.txt"
 listing.write_text("".join("file '"+str(p.resolve())+"'\n" for p in audios),encoding="utf-8")
 audio=TEMP/"joined.mp3"
 run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(listing),"-c","copy",str(audio)])
 final=OUT/f"{stem}.mp4"
 run(["ffmpeg","-y","-i",str(silent),"-i",str(audio),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",str(final)])
 return final
def upload(video,story):
 names=["YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET","YOUTUBE_REFRESH_TOKEN"]
 if not all(os.getenv(k) for k in names):
  print("YouTube upload skipped: OAuth secrets are not configured."); return None
 creds=Credentials(None,refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
  token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["YOUTUBE_CLIENT_ID"],
  client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],scopes=["https://www.googleapis.com/auth/youtube.upload"])
 yt=build("youtube","v3",credentials=creds)
 title=story.get("title","سبزیوں کی مزاحیہ کہانی")[:95]
 desc="اردو کی نئی مزاحیہ کارٹون کہانی!\nRocky Potato • Brock Broccoli • Caro Carrot • Tommy Tomato\n"+" ".join(story.get("hashtags",["#Shorts","#UrduComedy"]))
 body={"snippet":{"title":title,"description":desc,"tags":["Urdu comedy","Talking vegetables","Funny cartoon","Shorts"],"categoryId":"23"},
       "status":{"privacyStatus":os.getenv("YOUTUBE_PRIVACY","public"),"selfDeclaredMadeForKids":False}}
 return yt.videos().insert(part="snippet,status",body=body,media_body=MediaFileUpload(str(video),mimetype="video/mp4",resumable=True)).execute()
async def main():
 story=ai_story()
 print("\n=== TODAY'S CONTENT ===")
 print("Topic:",story.get("topic")); print("Title:",story.get("title"))
 for i,s in enumerate(story["scenes"],1): print(f"Scene {i}: {s['speaker']} — {s['line']} | Action: {s.get('action','')}")
 stem=datetime.now().strftime("vegetables_%Y%m%d_%H%M%S"); audios=[]
 for i,s in enumerate(story["scenes"],1):
  p=TEMP/f"voice_{i}.mp3"; await make_voice(s["line"],CAST[s["speaker"]]["voice"],p); audios.append(p)
 video=render(story,audios,stem)
 (OUT/f"{stem}_content.json").write_text(json.dumps(story,ensure_ascii=False,indent=2),encoding="utf-8")
 print("Video created:",video)
 result=upload(video,story)
 if result:
  info={"video_id":result.get("id"),"url":"https://youtu.be/"+result.get("id",""),"title":story.get("title")}
  (OUT/f"{stem}_youtube_upload.json").write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding="utf-8")
  print("YouTube upload:",info["url"])
if __name__=="__main__": asyncio.run(main())
