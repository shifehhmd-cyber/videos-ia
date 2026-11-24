import asyncio, json, edge_tts, subprocess
SENT = ["Quedan treinta y siete días para que acabe dos mil veintiséis.",
        "Hoy te has despertado.","Respiras.","Y estás leyendo esto.",
        "Millones de personas darían todo por tener solo eso.",
        "No esperes a enero.","Empieza hoy."]
async def one(i,t):
    c = edge_tts.Communicate(t, "es-ES-AlvaroNeural", rate="-8%", pitch="-2Hz",
                             boundary="WordBoundary", proxy="http://127.0.0.1:41863")
    words=[]; 
    with open(f"s{i}.mp3","wb") as f:
        async for ch in c.stream():
            if ch["type"]=="audio": f.write(ch["data"])
            elif ch["type"]=="WordBoundary":
                words.append((ch["offset"]/1e7, (ch["offset"]+ch["duration"])/1e7, ch["text"]))
    return words
async def main():
    out=[]
    for i,t in enumerate(SENT):
        w=await one(i,t)
        d=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f"s{i}.mp3"]))
        out.append({"text":t,"words":w,"dur":d})
    json.dump(out,open("timings.json","w"),ensure_ascii=False,indent=1)
asyncio.run(main())
