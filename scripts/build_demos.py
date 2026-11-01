"""Encode original AI-illustrated worker storyboards as renovation montage GIFs.
Requires FFmpeg. These are staged illustrations, not continuous contractor video.
The landing-page hero remains a separate manual before/after slider.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'frontend/public/demos'

def ffmpeg(*args):
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*map(str,args)],check=True)

for scene in ('living','bedroom'):
    with TemporaryDirectory(prefix='roomform-worker-frames-') as temporary:
        folder=Path(temporary)
        source=OUTPUT/'sources'/f'{scene}-workers.png'
        for frame in range(6):
            col,row=frame%3,frame//3
            ffmpeg('-i',source,'-vf',f'crop=trunc(iw/3):trunc(ih/2):trunc(iw/3)*{col}:trunc(ih/2)*{row},scale=560:560:force_original_aspect_ratio=increase,crop=560:560,setsar=1','-frames:v',1,folder/f'{frame}.png')
        # Fast work stages, pause on the finished room; no backwards unbuilding.
        durations=[.6,.45,.45,.45,.5,2.4]
        sequence=[]
        for i,duration in enumerate(durations):sequence.extend([f"file '{folder/(str(i)+'.png')}'",f'duration {duration}'])
        sequence.append(f"file '{folder/'5.png'}'")
        listing=folder/'frames.txt';listing.write_text('\n'.join(sequence)+'\n')
        graph='fps=12,split[frames][colors];[colors]palettegen=max_colors=128[palette];[frames][palette]paletteuse=dither=bayer:bayer_scale=4'
        ffmpeg('-f','concat','-safe',0,'-i',listing,'-filter_complex',graph,'-loop',0,OUTPUT/f'{scene}.gif')
        # A still from the same storyboard avoids camera jumps when pausing.
        ffmpeg('-i',folder/'5.png','-frames:v',1,'-q:v',3,OUTPUT/f'{scene}-poster.jpg')
        print(scene,(OUTPUT/f'{scene}.gif').stat().st_size,'bytes')
