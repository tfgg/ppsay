# -*- coding: utf-8 -*-
import json

cardinal_directions = ['North East', 'South East', 'South West', 'North West', 'North', 'South', 'East', 'West']

def generate_names(constituency):
    names = [constituency]
    name_tokens = constituency.split()

    # Transpose directions, e.g. Durham North -> North Durham
    for name in list(names):
        if ' and ' not in name:
            for direction in cardinal_directions:
              if constituency.endswith(direction):
                name_ = direction + " " + constituency[:-len(direction)].strip()
                names.append(name_)
                break

    # Replace " and " with " & "
    for name in list(names):
        if " and " in name:
            names.append(name.replace(" and ", " & "))

    # Undo commas, e.g. Durham, City of -> City of Durham
    # Also remove commas e.g. Sheffield, Hallam -> Sheffield Hallam
    # And remove first word, e.g. Shieffield, Hallam -> Hallam
    for name in list(names):
        if ',' in constituency:
            tokens = [x.strip() for x in constituency.split(',')]

            names.append(" ".join(tokens))

            if " and " not in constituency:
                names.append(" ".join(tokens[1:]))
                names.append(" ".join(reversed(tokens)))

    # Remove "upon tyne" to fix some Newcastle matching
    for name in list(names):
        if 'upon Tyne' in name:
            name_ = name.replace(' upon Tyne', '')
            names.append(name_)
     
    # Filter out Southamton, Test --> Test
    names = [x for x in names if x != 'test']

    return names

if __name__ == "__main__": 
    constituencies = json.load(open('parse_data/constituencies.json'))

    out = {}

    for constituency in constituencies:
        names = generate_names(constituency['name'])
        out[constituency['id'].split(':')[-1]] = names

    json.dump(out, open('parse_data/constituencies_other_names.json', 'w+'), indent=4, sort_keys=True)
