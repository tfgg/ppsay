# -*- coding: utf-8 -*-

def primary_generate_names(names, person):
    """
        Make primary names to match someone.

        These are used to find someone initially.
    """

    incumbent = person['incumbent']
    prefix = person['name_prefix'] 

    for name in names:
        name_tokens = name.split()

        # If we have more than forename-surname, try middlename + surname
        # Catches, e.g. Máirtín Ó Muilleoir
        if len(name_tokens) > 2:
            s = " ".join(name_tokens[1:])

            # Screw you Al Murray
            if s != u"Pub Landlord":
                yield s

            s = name_tokens[0] + " " + name_tokens[-1]

            if s != u"The Landlord":
                yield s

        # Macdonald -> Mcdonald
        if u" Mac" in name:
            yield name.replace('Mac', 'Mc')
        
        if incumbent:    
            yield u"MP {}".format(name)
            yield u"{} MP".format(name)

        if prefix is not None and prefix != "":
            yield u"{} {}".format(prefix, name)

general_titles = {'Dr', 'Cllr', 'Sir', 'Prof'}
male_titles = {'Mr'}
female_titles = {'Mrs', 'Miss', 'Ms'}
name_blacklist = {'pub', 'the', 'landlord', 'pub landlord', 'will'}

def secondary_generate_names(names, person):
    """
        Make extra (non-primary) names to match someone.

        These are only used when there's a primary match.
    """
    gender = person.get('gender')
    extra_names = []

    # Try to only match gender appropriate titles

    titles = general_titles
    if gender and gender.lower() == 'male':
        titles |= male_titles
    elif gender and gender.lower() == 'female':
        titles |= female_titles
    else:
        titles |= (male_titles | female_titles)


    for name in names:
        name_bits = name.split()

        extra_names.append(name_bits[0].lower())
        extra_names.append(name_bits[-1].lower())
        extra_names.append(" ".join(name_bits[-2:-1]).lower())

        for title in titles:
            extra_names.append(u"{} {}".format(title, name).lower())
            extra_names.append(u"{} {}".format(title, name_bits[-1]).lower())

        extra_names.append(u"Sir {}".format(name_bits[0]).lower())
    
    return set(extra_names) - name_blacklist
