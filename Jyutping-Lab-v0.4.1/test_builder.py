"""Offline fixture-based smoke test for the importer."""
import json, pathlib, tempfile
from build_dictionary import compile_dictionary


def run():
    with tempfile.TemporaryDirectory() as td:
        root=pathlib.Path(td); rime=root/'rime'; yyzd=root/'yyzd'; output=root/'data'
        rime.mkdir(); (yyzd/'dist/tsv').mkdir(parents=True)
        (rime/'jyut6ping3.chars.dict.yaml').write_text('---\nname: jyut6ping3.chars\n...\n行\thaang4\n行\thong4\n銀\tngan4\n街\tgaai1\n', encoding='utf-8')
        (rime/'jyut6ping3.words.dict.yaml').write_text('---\nname: jyut6ping3.words\n...\n銀行\tngan4 hong4\n行街\thaang4 gaai1\n', encoding='utf-8')
        (yyzd/'dist/tsv/jyutping-traditional.tsv').write_text(''.join(f'行\t行\thaang4\t行街\t走路\t\n' for _ in range(70)),encoding='utf-8')
        manifest=compile_dictionary(rime,yyzd,output,pathlib.Path(__file__).with_name('custom-words.csv'),False,False)
        chars=json.loads((output/'characters.json').read_text());assert chars['行'][0]['m']=='走路'
        assert chars['行'][0]['j']=='haang4'
        bucket=ord('銀')%32; words=json.loads((output/f'words-{bucket:02d}.json').read_text());assert words['銀行'][0]['j']=='ngan4 hong4'
        assert manifest['unique_words']>=4
        print('OK: dictionary merge, word shard, custom CSV, manifest')
if __name__=='__main__':run()
