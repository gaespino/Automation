Script output:
================================================================================
Debug Framework Release Notes Generator
================================================================================


STDERR:
Traceback (most recent call last):
  File "C:\Git\Automation\DEVTOOLS\generate_release_notes.py", line 480, in main
    generator.parse_deployment_reports()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "C:\Git\Automation\DEVTOOLS\generate_release_notes.py", line 62, in parse_deployment_reports
    print(f"\U0001f4ca Parsing deployment reports from {self.start_date.date()} to {self.end_date.date()}...")
    ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\gaespino\AppData\Local\Programs\Python\Python314\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f4ca' in position 0: character maps to <undefined>

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Git\Automation\DEVTOOLS\generate_release_notes.py", line 511, in <module>
    exit(main())
         ~~~~^^
  File "C:\Git\Automation\DEVTOOLS\generate_release_notes.py", line 502, in main
    print(f"\n\u274c Error: {e}")
    ~~~~~^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\gaespino\AppData\Local\Programs\Python\Python314\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'charmap' codec can't encode character '\u274c' in position 2: character maps to <undefined>


(No DRAFT_RELEASE_*.md found in deploys/)