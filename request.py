"""Emit worker-comfyui request: python request.py reference.png > request.json."""
import argparse
import base64
import json
from pathlib import Path


def make_workflow(prompt, width=832, height=480, length=124, seed=424242):
    def n(kind, **inputs):
        return {'class_type': kind, 'inputs': inputs}
    return {
        'unet': n('UNETLoader', unet_name='minimax_h3_ref2va_pruned_int8_convrot.safetensors', weight_dtype='default'),
        'clip': n('CLIPLoader', clip_name='qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors', type='minimax', device='default'),
        'vae_video': n('VAELoader', vae_name='minimax_h3_video_vae_fp16.safetensors'),
        'vae_audio': n('VAELoader', vae_name='minimax_h3_audio_vae_fp32.safetensors'),
        'reference': n('LoadImage', image='reference.png'),
        'cond': n('MiniMaxH3ReferenceToVideo', clip=['clip', 0], vae=['vae_video', 0], audio_vae=['vae_audio', 0], prompt=prompt,
                  width=width, height=height, length=length, ref_image_size='match', **{'ref_images.ref_image_0': ['reference', 0]}),
        'noise': n('RandomNoise', noise_seed=seed),
        'guider': n('BasicGuider', model=['unet', 0], conditioning=['cond', 0]),
        'sampler_select': n('KSamplerSelect', sampler_name='res_multistep'),
        'sigmas': n('BasicScheduler', model=['unet', 0], scheduler='simple', steps=20, denoise=1.0),
        'sample': n('SamplerCustomAdvanced', noise=['noise', 0], guider=['guider', 0], sampler=['sampler_select', 0], sigmas=['sigmas', 0], latent_image=['cond', 1]),
        'decode_video': n('VAEDecode', samples=['sample', 0], vae=['vae_video', 0]),
        'decode_audio': n('VAEDecodeAudio', samples=['sample', 0], vae=['vae_audio', 0]),
        'video': n('CreateVideo', images=['decode_video', 0], fps=24, audio=['decode_audio', 0]),
        'save': n('SaveVideo', video=['video', 0], filename_prefix='video/H3_REF2V', format='mp4', codec='h264'),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('reference', type=Path)
    parser.add_argument('--prompt', default='The adult character from <Picture 1> smiles softly and turns her head toward the camera. A steady cinematic shot, natural movement, quiet room ambience.')
    args = parser.parse_args()
    raw = args.reference.read_bytes()
    if not raw.startswith(b'\x89PNG\r\n\x1a\n'):
        parser.error('Provide a PNG reference image')
    print(json.dumps({'input': {'workflow': make_workflow(args.prompt), 'images': [{'name': 'reference.png', 'image': base64.b64encode(raw).decode()}]}}))
