#!/usr/bin/python3
#
# Script to
# 1) build source CSV files for translation, suitable for automatic input into Crowdin.
#    That means:
#    - English,
#    - one translation per line,
#    - consistent column ordering,
#    - stable identifier column,
# 2) Crowdin-generated translations to create files compatible with the existing rs.tdwg.org scripts.
#
# Matthew Blissett, 2022-02, CC0

import os
import re
import csv
from collections import OrderedDict

# Source (English) files to push to Crowdin.
termfiles_to_translate = [
    'terms/terms',
#    'establishmentMeans/establishmentMeans',
#    'degreeOfEstablishment/degreeOfEstablishment',
#    'pathway/pathway'
]

# From those source files, these columns will be made available for translation
translate_these_columns = {
    'label': 'Label',
    'rdfs_comment': 'Comment',
    'dcterms_description': 'Description',
    'examples': 'Examples',
    'definition': 'Definition',
    'notes': 'Notes'
}

# Output structure (defined in crowdin.yml)
# identifier,context,source_or_translation
crowdin_fieldnames = ['identifier', 'context', 'text']

# Fields to be output into the *-translations.csv file
# TODO: add other fields, comment_…, description_…, examples_…, notes_…
output_translation_columns = {
    'label': 'label',
    'dcterms_description': 'definition'
}

for termfile in termfiles_to_translate:
    print("Processing source file "+termfile+".csv")

    # Output file with column names known to Crowdin
    with open(termfile+'.en.csv', 'w', newline='') as crowdinEnglishFile:
        crowdinEnglishTerms = csv.writer(crowdinEnglishFile, quoting=csv.QUOTE_MINIMAL, lineterminator=os.linesep)
        crowdinEnglishTerms.writerow(crowdin_fieldnames)

        # Input file
        with open(termfile+'.csv', newline='') as originalTermsFile:
            originalTerms = csv.DictReader(originalTermsFile)

            for originalRow in originalTerms:
                # Don't (yet) bother translating deprecated terms
                if originalRow['term_deprecated'] != "true":
                    # Find any columns eligible for translation
                    for translatableCol in translate_these_columns.keys():
                        if translatableCol in originalRow.keys() and len(originalRow[translatableCol]) > 0:
                            if translatableCol == 'examples':
                                # Remove the `quoted` examples, and see if there's any notes to translate
                                pattern = '`[^`]+`[;., \n]*'
                                examples_without_examples = re.sub(pattern, '', originalRow[translatableCol])
                                if len(examples_without_examples) < 2:
                                    continue

                            identifier = originalRow['term_localName']+":"+translatableCol
                            context = translate_these_columns[translatableCol]+" for "+originalRow['label'] + ' http://rs.tdwg.org/dwc/terms/'+originalRow['term_localName']
                            crowdinEnglishTerms.writerow([identifier, context, originalRow[translatableCol]])

    print("Generating file "+termfile+"-translations.csv")

    # Read any *.??.csv files (produced by Crowdin) and generate a *-translations.csv file
    with open(termfile+'-translations.csv', 'w', newline='') as translationsFile:
        languages = ['en','de','es','fr','ko','nl','ru','zh-Hans', 'zh-Hant']

        # *-translations.csv file has columns
        # term_localName,label_en,label_…,definition_en,definition_…
        fieldnames = ['term_localName']
        # GitHub won't format the CSV nicely with this comment included.
        # translationsFile.write("# This file is generated by the script in process/translations.\n")
        translationsFile.write('term_localName')
        for col in output_translation_columns.keys():
            for lang in languages:
                fieldnames += col+'_'+lang
                translationsFile.write(","+output_translation_columns[col]+"_"+lang)
        translationsFile.write("\n")

        # Record each term in a dictionary with entries label_en etc.
        combinedTranslations = OrderedDict()

        xfieldnames = ['identifier', 'context', 'text']

        for lang in languages:
            if (os.path.exists(termfile+'.'+lang+'.csv')):
                print("  Reading "+termfile+'.'+lang+'.csv')
                with open(termfile+'.'+lang+'.csv', newline='') as oneLanguageFile:
                    oneLanguageTerms = csv.DictReader(oneLanguageFile)

                    for row in oneLanguageTerms:
                        wholeIdentifier = row['identifier'] # e.g. basisOfRecord:label
                        text = row['text']

                        (localName, column) = wholeIdentifier.split(':')
                        if localName not in combinedTranslations:
                            combinedTranslations[localName] = dict()
                        combinedTranslations[localName][column+'_'+lang] = text

        # Write a row with a term and the translations
        for localName, translations in combinedTranslations.items():
            translationsFile.write(localName)
            for col in output_translation_columns.keys():
                for lang in languages:
                    if col+"_"+lang in translations:
                        text = translations[col+"_"+lang]
                        text = text.replace('"', '""')
                        if ',' in text or '"' in text:
                            translationsFile.write(',"'+text+'"')
                        else:
                            translationsFile.write(','+text)
            translationsFile.write("\n")

    print("  Done.")
