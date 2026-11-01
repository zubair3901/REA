"""Build credited, illustrative before/after GIFs. Requires ffmpeg on PATH."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / 'frontend/public/images'
OUTPUT = ROOT / 'frontend/public/demos'
OUTPUT.mkdir(exist_ok=True)
# Hold before, reveal after, hold after, then return to the starting view.
progress = 'if(lt(T,1),0,if(lt(T,3),(T-1)/2,if(lt(T,4.5),1,if(lt(T,6.5),1-(T-4.5)/2,0))))'
for scene in ('living', 'bedroom'):
    normalize = 'fps=10,scale=560:374:force_original_aspect_ratio=increase,crop=560:374,setsar=1,format=rgb24'
    graph = (
        f'[0:v]{normalize}[before];[1:v]{normalize}[after];'
        f"[before][after]blend=all_expr='if(lt(X,W*({progress})),B,A)',"
        'trim=duration=7,split[frames][colors];'
        '[colors]palettegen=max_colors=96:stats_mode=diff[palette];'
        '[frames][palette]paletteuse=dither=bayer:bayer_scale=4'
    )
    subprocess.run([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-loop', '1', '-t', '7', '-i', str(IMAGES / f'{scene}-before.png'),
        '-loop', '1', '-t', '7', '-i', str(IMAGES / f'{scene}.jpg'),
        '-filter_complex', graph, '-loop', '0', str(OUTPUT / f'{scene}.gif'),
    ], check=True)
    print(scene, (OUTPUT / f'{scene}.gif').stat().st_size, 'bytes')
