#!/usr/bin/env python3
"""Build a static Jyutping dictionary from public GitHub repositories.
Sources: rime/rime-cantonese (CC BY 4.0), kfcd/yyzd (CC BY 3.0).
No Python dependencies outside the standard library; no network at runtime on the website.
"""
from __future__ import annotations
import argparse, csv, datetime as dt, json, pathlib, re, subprocess, tempfile, collections

ROOT = pathlib.Path(__file__).resolve().parent
SOUND = re.compile(r'^[a-z]+[1-6]$')
SEPARATOR = re.compile(r'[/,;、，；]+')
CHECKED = str.maketrans({'7': '1', '8': '3', '9': '6'})
SHARDS = 32


def run(*args: str) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True, encoding='utf-8')
    return result.stdout.strip()


def clone(slug: str, folder: pathlib.Path):
    print(f'Downloading https://github.com/{slug} ...', flush=True)
    run('git', 'clone', '-q', '--depth', '1', f'https://github.com/{slug}.git', str(folder))


def revision(folder: pathlib.Path) -> str:
    try:
        return run('git', '-C', str(folder), 'rev-parse', '--short=12', 'HEAD')
    except Exception:
        return 'local'


def normalize_syllable(text: str) -> str:
    value = text.strip().lower().translate(CHECKED)
    return value if SOUND.fullmatch(value) else ''


def split_readings(raw: str) -> list[str]:
    # kfcd lists variants separated by slashes; keep syllabic tones distinct.
    return list(dict.fromkeys(x for chunk in SEPARATOR.split(raw) if (x := normalize_syllable(chunk))))


def new_entry():
    return {'e': [], 'm': '', 's': []}  # examples, meaning, sources


def add_char(chars: dict, char: str, sound: str, source: str, meaning: str = '', examples=None):
    if len(char) != 1 or not SOUND.fullmatch(sound):
        return
    item = chars.setdefault(char, {}).setdefault(sound, new_entry())
    if source not in item['s']:
        item['s'].append(source)
    if meaning and (source == 'custom' or not item['m']):
        item['m'] = meaning.strip()
    for example in (examples or []):
        example = example.strip()
        if example and example not in item['e'] and len(item['e']) < 9:
            item['e'].append(example)


def read_rime_lines(file: pathlib.Path):
    if not file.is_file():
        raise FileNotFoundError(f'Rime source missing: {file}')
    inside = False
    for line in file.open(encoding='utf-8-sig'):
        line = line.rstrip('\r\n')
        if not inside:
            inside = line.strip() == '...'
            continue
        if not line or line.startswith('#'):
            continue
        fields = line.split('\t')
        if len(fields) >= 2:
            yield fields[0].strip(), fields[1].strip()


def find_yyzd_jyutping_file(root: pathlib.Path) -> pathlib.Path:
    # Pick from preconverted variants, never parse the original Yale-romanized yyzd.txt as Jyutping.
    candidates = [p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in ('.tsv', '.csv') and 'dist' in p.parts]
    scores = []
    for file in candidates:
        try:
            with file.open(encoding='utf-8-sig') as fh:
                sample = fh.readlines()
        except (OSError, UnicodeError):
            continue
        count = 0
        evidence = 0
        for ln in sample:
            fields = ln.rstrip('\r\n').split('\t' if file.suffix == '.tsv' else ',')
            if len(fields) < 5:
                continue
            if split_readings(fields[2]):
                count += 1
            # Yale spellings are different for these specific pairs. Both are known Jyutping examples.
            if fields[0] == '浚' and 'zeon3' in fields[2]:
                evidence += 10
            if fields[0] == '長' and 'coeng4' in fields[2]:
                evidence += 10
            if fields[0] == '鴉' and 'aa1' in fields[2]:
                evidence += 1
        name = file.name.lower()
        if 'jyutping' in name or 'jyut' in name:
            evidence += 100
        if 'traditional' in name or 'trad' in name or '繁' in name:
            evidence += 8
        if count > 50:
            scores.append((evidence, count, file))
    if not scores or max(scores)[0] < 8:
        raise RuntimeError('Cannot identify a verified Jyutping TSV in kfcd/yyzd/dist. Refusing to confuse Yale with Jyutping.')
    winner = max(scores, key=lambda s:(s[0],s[1]))[2]
    print(f'KFCD Jyutping input: {winner.relative_to(root)}')
    return winner


def load_yyzd(chars: dict, file: pathlib.Path) -> int:
    total = 0
    delim = '\t' if file.suffix.lower() == '.tsv' else ','
    with file.open(encoding='utf-8-sig', newline='') as fh:
        for fields in csv.reader(fh, delimiter=delim):
            if len(fields) < 5:
                continue
            char = fields[0].strip()
            if len(char) != 1:
                continue
            sounds = split_readings(fields[2]); examples = re.split('[，,；;]', fields[3]); meaning = fields[4]
            # A source row with multiple readings may group distinct contexts.
            # Do not assign one row's definition/examples to every tone without evidence.
            for sound in sounds:
                add_char(chars, char, sound, 'yyzd', meaning if len(sounds) == 1 else '', examples if len(sounds) == 1 else [])
                total += 1
    return total


def load_custom(chars: dict, words: dict, csv_file: pathlib.Path) -> int:
    if not csv_file.exists():
        raise FileNotFoundError(csv_file)
    n = 0
    with csv_file.open(encoding='utf-8-sig', newline='') as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader, start=2):
            word = (row.get('字詞') or '').strip()
            reading = (row.get('粵拼') or '').strip().lower()
            meaning = (row.get('解釋') or '').strip()
            examples = [x.strip() for x in re.split('[、,，；;]', row.get('詞例') or '') if x.strip()]
            if not word and not reading:
                continue
            syllables = [normalize_syllable(x) for x in reading.split()]
            if not word or not syllables or any(not x for x in syllables) or len(word) != len(syllables):
                print(f'WARNING custom-words.csv row {i}: invalid grapheme/syllable count: {word!r} {reading!r}')
                continue
            if len(word) == 1:
                add_char(chars, word, syllables[0], 'custom', meaning, examples)
            else:
                add_word(words, word, ' '.join(syllables), 'custom', meaning)
            n += 1
    return n


def add_word(words: dict, word: str, reading: str, source: str, meaning: str = ''):
    syllables = reading.split()
    if not word or len(word) != len(syllables) or any(not SOUND.fullmatch(x) for x in syllables):
        return
    readings = words.setdefault(word, {})
    record = readings.setdefault(reading, {'s': [], 'm': ''})
    if source not in record['s']:
        record['s'].append(source)
    if meaning and (source == 'custom' or not record['m']):
        record['m'] = meaning


def load_rime(chars: dict, words: dict, root: pathlib.Path, include_phrases: bool) -> dict:
    char_path = root/'jyut6ping3.chars.dict.yaml'
    word_paths = [root/'jyut6ping3.words.dict.yaml']
    if include_phrases:
        word_paths.append(root/'jyut6ping3.phrase.dict.yaml')
    n_chars = 0; n_words = 0
    for char, sound in read_rime_lines(char_path):
        sound = normalize_syllable(sound)
        if sound and len(char) == 1:
            add_char(chars, char, sound, 'rime'); n_chars += 1
    for file in word_paths:
        for word, reading in read_rime_lines(file):
            syl = [normalize_syllable(s) for s in reading.split()]
            if len(word) < 2 or len(word) != len(syl) or any(not s for s in syl):
                continue
            add_word(words, word, ' '.join(syl), 'rime'); n_words += 1
    return {'rime_character_rows': n_chars, 'rime_word_rows': n_words}


def enrich_examples(chars: dict, words: dict):
    # Evidence-based examples: only words where the aligned Jyutping syllable matches.
    pending = collections.defaultdict(list)
    for word, readings in words.items():
        if not (2 <= len(word) <= 5):
            continue
        for jyutping in readings:
            for char, syllable in zip(word, jyutping.split()):
                k = (char, syllable)
                if char in chars and syllable in chars[char] and len(pending[k]) < 25:
                    pending[k].append(word)
    for char, readings in chars.items():
        for syllable, item in readings.items():
            for word in sorted(set(pending.get((char,syllable),[])), key=lambda x:(len(x), x)):
                if len(item['e']) >= 5:
                    break
                if word not in item['e']:
                    item['e'].append(word)


def save_compact(file: pathlib.Path, obj):
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(obj, ensure_ascii=False, separators=(',',':')), encoding='utf-8')


def compile_dictionary(rime: pathlib.Path, yyzd: pathlib.Path, output: pathlib.Path, custom: pathlib.Path, include_phrases: bool, validate: bool):
    chars = {}; words = {}
    metrics = load_rime(chars, words, rime, include_phrases)
    source = find_yyzd_jyutping_file(yyzd)
    metrics['yyzd_rows'] = load_yyzd(chars, source)
    metrics['custom_rows'] = load_custom(chars, words, custom)
    enrich_examples(chars, words)
    print(f'Preparing {len(chars):,} characters and {len(words):,} distinct words...')
    if validate and (len(chars) < 15000 or len(words) < 50000 or metrics['yyzd_rows'] < 800):
        raise RuntimeError(f'Unexpectedly small input data, stopping deployment: {metrics}')
    # char records use short fields to minimize the footprint of large public datasets.
    char_records = {c:[{'j':j,**record} for j,record in sorted(readings.items())] for c, readings in chars.items()}
    save_compact(output/'characters.json',char_records)
    shards = [dict() for _ in range(SHARDS)]
    for word,readings in words.items():
        idx = ord(word[0]) % SHARDS
        shards[idx][word] = [{'j':j, **row} for j,row in sorted(readings.items())]
    for i, shard in enumerate(shards):
        save_compact(output/f'words-{i:02d}.json', shard)
    metrics['unique_characters'] = len(chars)
    metrics['unique_char_readings'] = sum(len(v) for v in chars.values())
    metrics['unique_words'] = len(words)
    metrics['unique_word_readings'] = sum(len(v) for v in words.values())
    metrics['shards'] = SHARDS
    manifest = {'built':True, 'edition':'0.4.1', 'built_at':dt.datetime.now(dt.timezone.utc).isoformat(),
      'source_revisions':{'rime':revision(rime),'kfcd_yyzd':revision(yyzd)},
      'source_paths':{'yyzd':str(source.relative_to(yyzd))}, **metrics}
    save_compact(output/'manifest.json',manifest)
    print('Output:', output, json.dumps(metrics,ensure_ascii=False))
    return manifest


def main():
    p=argparse.ArgumentParser(description='Import Rime Cantonese + KFCD YYZD + custom-words.csv')
    p.add_argument('--rime-dir', type=pathlib.Path)
    p.add_argument('--yyzd-dir', type=pathlib.Path)
    p.add_argument('--output', type=pathlib.Path,default=ROOT/'data')
    p.add_argument('--custom', type=pathlib.Path,default=ROOT/'custom-words.csv')
    p.add_argument('--no-phrases', action='store_true',help='Exclude phrase dictionary to reduce size')
    p.add_argument('--allow-small',action='store_true',help='Allow small sample fixtures (tests only)')
    args=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='jyutlab-') as tmp:
        temp=pathlib.Path(tmp)
        rime=args.rime_dir or temp/'rime'
        yyzd=args.yyzd_dir or temp/'yyzd'
        if not args.rime_dir: clone('rime/rime-cantonese',rime)
        if not args.yyzd_dir: clone('kfcd/yyzd',yyzd)
        compile_dictionary(rime, yyzd, args.output, args.custom,not args.no_phrases, not args.allow_small)
if __name__=='__main__':main()
