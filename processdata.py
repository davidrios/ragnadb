import json
import re
from base64 import b32encode
from html.parser import HTMLParser
from collections import defaultdict, namedtuple
from hashlib import md5
from pathlib import Path

COLORS_RE = re.compile(r'\^[0-9A-Fa-f]{6}')
Item = namedtuple('Item', 'id name desc res ilus prefix')
Desc = namedtuple('Desc', 'text props')

MAP_PROPS = {
    # 'Applicable job': 'Classe',
    'Ataque': 'attack',
    # 'Class': 'Classe',
    # 'Classe aplicável': 'Classe',
    # 'Classe': 'Classe',
    # 'Classes que utilizam': 'Classe',
    # 'Classes que utlizam': 'Classe',
    # 'Classes': 'Classe',
    'Combina com': 'useOn',
    'Def': 'defense',
    'Def.': 'defense',
    'Defense': 'defense',
    'Defesa': 'defense',
    # 'Duração': 'Duração',
    'Elemento': 'element',
    'Equipa em': 'equipIn',
    'Equipado em': 'equipIn',
    'Equipar em': 'equipIn',
    'Equipe em': 'equipIn',
    'Força de ataque': 'attack',
    'Forçca de ataque': 'attack',
    'Head position': 'equipIn',
    # 'Job': 'Classe',
    'Limite de nível': 'maximumLevel',
    # 'Negociação': 'Negociação',
    'Nivel necessário': 'minimumLevel',
    'Nv. mínimo necessário': 'minimumLevel',
    'Níveis permitidos': 'minimumLevel',
    'Nível da arma': 'weaponLevel',
    'Nível limite': 'maximumLevel',
    'Nível mínimo': 'minimumLevel',
    'Nível necessário': 'minimumLevel',
    'Nível necessário.': 'minimumLevel',
    'Nível necesário': 'minimumLevel',
    'Nível requerido': 'minimumLevel',
    'Nível requisitado': 'minimumLevel',
    'Peso': 'weigth',
    'Posição': 'equipIn',
    # 'Profissões que utilizam': 'Classe',
    'Propriedade': 'element',
    'Required lv': 'minimumLevel',
    'Tipo de arma': 'itemType',
    'Tipo de item': 'itemType',
    'Tipo': 'itemType',
    'Type': 'itemType',
    'Usado em': 'equipIn',
    # 'Utilização': 'useOn',
}


def nt2dict(nt):
    return dict((field, getattr(nt, field)) for field in nt._fields)


def genfname(reference):
    if isinstance(reference, str):
        reference = reference.encode('utf8')

    digest = md5(reference).digest()
    xorfolded = bytearray(a ^ b for a, b in zip(digest[:8], digest[8:]))

    return b32encode(xorfolded).decode('ascii').strip('=').lower()


def processprops(text):
    props = defaultdict(set)
    lines = text.splitlines()
    for line in lines:
        vals = line.split(':')
        if len(vals) != 2:
            continue

        propname = MAP_PROPS.get(vals[0].strip(' :').capitalize())
        if propname is None:
            continue

        val = vals[1].strip(' :')

        # several workarounds
        if propname == 'itemType' and val == 'Neutro':
            props['element'].add(val)
        elif propname.startswith('Classe') and 'Equipamento' in val and 'Carta' not in props['itemType']:
            props['itemType'].add(val)
        elif propname == 'equipIn' and val == '1':
            continue
        elif propname == 'weigth' and val == '1#':
            props[propname].add('1')
        else:
            props[propname].add(val)

    if 'weigth' in props and len(props['weigth']) > 1 and 'caixa' in ''.join(line.lower() for line in lines[:3]):
        props['weigth'] = set('1')

    props = {prop: vals.pop() for prop, vals in props.items()}

    for splitprop in ['Classe', 'equipIn']:
        if splitprop not in props:
            continue

        props[splitprop] = set(
            sorted(
                i.strip().capitalize()
                for i in re.split(r'\s*[,/]\s*', re.sub(r'\s+[eE]\s+', ', ', props[splitprop]))
            )
        )

    if 'Classe' in props and 'Ovo de monstro' in props['Classe']:
        import pdb; pdb.set_trace()

    return props


def processdesc(text):
    if text is None:
        return None

    text = re.sub(r'\<NAVI\>.+\</NAVI\>\n', '', text)

    colors = ['^000000'] + COLORS_RE.findall(text)
    segments = COLORS_RE.split(text)

    html_text = []
    for idx, segment in enumerate(segments):
        color = colors[idx]
        if color != '^000000':
            segment = f'<span style="color: #{color[1:]}">{segment}</span>'

        html_text.append(segment)

    html_text = ''.join(html_text)

    return Desc(
        html_text.replace('\n', '<br />\n'),
        processprops(''.join(segments))
    )


def processtable(fpath):
    with fpath.open('rb') as fp:
        contents = fp.read().decode('latin1').splitlines()

    table = defaultdict(list)

    current = None
    for line in contents:
        line = line.strip()

        if re.match(r'^\d+#', line):
            current, text = line.split('#', 1)
            if text:
                table[current].append(text.strip('#'))
                current = None

            continue
        elif line == '#':
            current = None
            continue

        if current is not None:
            table[current].append(line)

    return {int(key): '\n'.join(val) for key, val in table.items()}


def processitem(item):
    props = item.desc.props if item.desc else {}
    for name, val in props.items():
        if name in {'attack', 'defense', 'minimumLevel', 'maximumLevel', 'weigth'}:
            try:
                props[name] = float(val)
            except ValueError:
                props[name] = 0
        elif isinstance(val, set):
            props[name] = list(val)

    item_json = {
        'id': item.id,
        'name': item.name,
        'res': genfname(item.res) if item.res else None,
        'text': item.desc.text if item.desc else '',
        'props': props,
        'ilus': genfname(item.ilus) if item.ilus else None,
        'prefix': item.prefix
    }

    return item_json


def processdata(data_dir):
    data_dir = Path(data_dir)

    nametable = processtable(data_dir / 'raw' / 'idnum2itemdisplaynametable.txt')
    restable = processtable(data_dir / 'raw' / 'idnum2itemresnametable.txt')
    desctable = processtable(data_dir / 'raw' / 'idnum2itemdesctable.txt')
    ilustable = processtable(data_dir / 'raw' / 'num2cardillustnametable.txt')
    prefixtable = processtable(data_dir / 'raw' / 'cardprefixnametable.txt')

    items = {
        iid: Item(
            iid,
            name.replace('_', ' '),
            processdesc(desctable.get(iid)),
            restable.get(iid),
            ilustable.get(iid),
            prefixtable.get(iid)
        ) for iid, name in nametable.items()
    }

    allprops = defaultdict(list)
    for item in items.values():
        if not item.desc:
            continue

        for prop, val in item.desc.props.items():
            allprops[prop].append(val)

    from collections import Counter
    from itertools import chain

    metaprops = defaultdict(set)

    for item in items.values():
        if not item.desc:
            continue

        for prop, val in item.desc.props.items():
            if prop not in {'element', 'equipIn', 'weaponLevel', 'itemType', 'useOn'}:
                continue

            if prop in {'Classe', 'equipIn'}:
                metaprops[prop] = metaprops[prop] | val
            else:
                metaprops[prop].add(val)

    for prop, vals in metaprops.items():
        metaprops[prop] = list(vals)

    source_paths = {
        'ilus': (data_dir / 'raw' / 'images' / 'data' / 'texture' / 'À¯ÀúÀÎÅÍÆäÀÌ½º' / 'cardbmp'),
        'sprite': (data_dir / 'raw' / 'images' / 'data' / 'texture' / 'À¯ÀúÀÎÅÍÆäÀÌ½º' / 'item'),
        'item': (data_dir / 'raw' / 'images' / 'data' / 'texture' / 'À¯ÀúÀÎÅÍÆäÀÌ½º' / 'collection')
    }

    save_paths = {
        'ilus': (data_dir / 'processed' / 'images' / 'cards'),
        'sprite': (data_dir / 'processed' / 'images' / 'sprite'),
        'item': (data_dir / 'processed' / 'images' / 'item')
    }

    for path in save_paths.values():
        path.mkdir(parents=True, exist_ok=True)

    items_json = {}
    for iid, item in items.items():
        processed_item = processitem(item)
        items_json[iid] = processed_item

        for ptype, path in source_paths.items():
            if ptype == 'ilus':
                fname = item.ilus
            else:
                fname = item.res

            if fname is None:
                continue

            fname = fname.split('\n')[-1]

            source_file = path / f'{fname}.bmp'
            try:
                source_file.rename(save_paths[ptype] / f'{genfname(fname)}.bmp')
            except FileNotFoundError:
                pass

    res_json = {
        'metaprops': metaprops,
        'items': items_json
    }

    with (data_dir / 'processed' / 'db.json').open('w') as fp:
        json.dump(res_json, fp)


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('data_dir')

    args = parser.parse_args()

    processdata(args.data_dir)


if __name__ == '__main__':
    main()
