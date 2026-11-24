import numpy as np, wave
SR=44100; DUR=26.0; BPM=70; beat=60/BPM
rng=np.random.default_rng(7)
out=np.zeros(int(SR*DUR)+SR*8)
def midi(n): return 440*2**((n-69)/12)
def note(t0,n,vel,length=3.5):
    f=midi(n); N=int(SR*length); t=np.arange(N)/SR
    s=np.zeros(N)
    B=0.0004
    for k in range(1,9):
        fk=f*k*np.sqrt(1+B*k*k)
        if fk>SR/2.2: break
        amp=(1/k**1.6)*np.exp(-t*(0.9+0.55*k)*(f/260)**0.35)
        s+=amp*np.sin(2*np.pi*fk*t+rng.uniform(0,6.28))
    att=np.minimum(1,t/0.004); s*=att
    # hammer thump
    s[:400]+=rng.normal(0,0.02,400)*np.linspace(1,0,400)
    i=int(t0*SR); out[i:i+N]+=vel*s
# Progression: Fmaj7, C/E, Am7, G(sus)  in C major, warm
chords=[(41,[60,64,65,69]),(40,[60,64,67,72]),(45,[60,64,67,69]),(43,[59,62,67,71])]*3
t=0.0; bar=4*beat
pat=[0,2,1,3,2,1,3,2]   # eighth-note arpeggio indices
for ci,(bass,ch) in enumerate(chords):
    if t>DUR: break
    note(t,bass,0.55,5); note(t,bass+12,0.25,5)
    for j,p in enumerate(pat):
        v=0.20+0.06*(j==0)+rng.uniform(-0.03,0.03)
        note(t+j*beat/2+rng.uniform(0,0.012),ch[p],v,3)
    # gentle melody note on beat 3 every other bar
    if ci%2==1: note(t+2*beat,ch[-1]+12,0.16,4)
    t+=bar
out=out[:int(SR*DUR)]
# simple lowpass
k=np.ones(5)/5; out=np.convolve(out,k,'same')
# reverb
L=int(SR*2.8); ir=rng.normal(0,1,L)*np.exp(-np.arange(L)/SR*2.6); ir[0]=0
from numpy.fft import rfft,irfft
n=len(out)+L; nf=1<<(n-1).bit_length()
wet=irfft(rfft(out,nf)*rfft(ir,nf),nf)[:len(out)]
wet/=np.max(np.abs(wet)); dry=out/np.max(np.abs(out))
mix=0.65*dry+0.45*wet
# fades
fi=int(SR*1.5); fo=int(SR*3)
mix[:fi]*=np.linspace(0,1,fi); mix[-fo:]*=np.linspace(1,0,fo)
mix=mix/np.max(np.abs(mix))*0.8
st=np.stack([mix,np.roll(mix,int(SR*0.012))],1)
with wave.open("music.wav","wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st*32767).astype(np.int16).tobytes())
