import math, wave
import numpy as np
def piano(path,seconds,seed):
    SR=44100; rng=np.random.default_rng(seed); bpm=[66,70,74,62][seed%4]; beat=60/bpm
    out=np.zeros(int(SR*(seconds+8)))
    def note(t0,n,vel,length):
        f=440*2**((n-69)/12); N=int(SR*length); tt=np.arange(N)/SR; s=np.zeros(N)
        for k in range(1,9):
            fk=f*k*math.sqrt(1+0.0004*k*k)
            if fk>SR/2.2: break
            s+=(1/k**1.6)*np.exp(-tt*(0.9+0.55*k)*(f/260)**0.35)*np.sin(2*np.pi*fk*tt+rng.uniform(0,6.28))
        s*=np.minimum(1,tt/0.004); i=int(t0*SR); out[i:i+N]+=vel*s
    progs=[[(41,[60,64,65,69]),(40,[60,64,67,72]),(45,[60,64,67,69]),(43,[59,62,67,71])],
           [(45,[57,60,64,67]),(41,[57,60,65,69]),(48,[55,60,64,67]),(43,[55,59,62,67])],
           [(38,[57,62,65,69]),(43,[59,62,65,67]),(36,[55,60,64,67]),(45,[57,60,64,69])],
           [(40,[59,64,67,71]),(36,[60,64,67,71]),(43,[59,62,67,71]),(38,[57,62,66,69])]]
    prog=progs[seed%4]; pat=[0,2,1,3,2,1,3,2]; t=0.0; ci=0
    while t<seconds:
        bass,ch=prog[ci%4]; note(t,bass,0.55,5); note(t,bass+12,0.22,5)
        for j,p in enumerate(pat): note(t+j*beat/2+rng.uniform(0,0.012),ch[p],0.2+0.06*(j==0)+rng.uniform(-.03,.03),3)
        if ci%2: note(t+2*beat,ch[-1]+12,0.15,4)
        t+=4*beat; ci+=1
    out=np.convolve(out[:int(SR*seconds)],np.ones(5)/5,'same')
    L=int(SR*2.8); ir=rng.normal(0,1,L)*np.exp(-np.arange(L)/SR*2.6); ir[0]=0
    nf=1<<(len(out)+L-1).bit_length(); wet=np.fft.irfft(np.fft.rfft(out,nf)*np.fft.rfft(ir,nf),nf)[:len(out)]
    mix=0.65*out/np.max(np.abs(out))+0.45*wet/np.max(np.abs(wet))
    fi,fo=int(SR*1.2),int(SR*2.5); mix[:fi]*=np.linspace(0,1,fi); mix[-fo:]*=np.linspace(1,0,fo)
    mix=mix/np.max(np.abs(mix))*0.8; st=np.stack([mix,np.roll(mix,int(SR*0.012))],1)
    with wave.open(path,"wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes())
