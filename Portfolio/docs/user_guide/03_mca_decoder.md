# MCA Single Decoder

URL: `/thr-tools/mca-decoder`

## Purpose
Decode raw Machine Check Architecture (MCA) hex values into human-readable register fields.

## Usage
1. Select **Product** (GNR / CWF / DMR)
2. Select **Error Type**
3. Enter hex values — one per line — in the Hex Input box, **or** upload a text file
4. Click **Decode**
5. Results appear in the AG Grid table (Register / Field / Value columns)

## Backend
`THRTools/Decoder/decoder.py` — `mcadata` class
