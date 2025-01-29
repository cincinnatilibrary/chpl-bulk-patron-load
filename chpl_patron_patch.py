import datetime
import pandas as pd

class StudentNew:
    """
    Defines a CUSTOMIZED patron record object for use with the API.
    """
    def __init__(
        self,
        last_name,
        first_name,
        barcode,
        student_id,
        school_district,
        pin,
        school,
        birth_date,
        phone_number,
        home_legal_address,
        home_legal_address_city,
        home_legal_address_state,
        home_legal_address_zip,
        notice_pref=None,
        email_address=None,
        home_library_code=None,
        patron_agency=None,
        alt_id=None,
        years_until_expiration=3
    ):
        """
        :param birth_date: a pandas Timestamp (or python datetime) for the child's DOB
        :param years_until_expiration: e.g. 3, to set the expiration date as today + 3 years
        """
        # ---------------------------------------------------------------------
        # 1) Normalize/parse birth_date if possible
        # ---------------------------------------------------------------------
        self.birth_date_obj = None

        # If already datetime-like:
        if isinstance(birth_date, (pd.Timestamp, datetime.datetime, datetime.date)):
            self.birth_date_obj = birth_date
        else:
            # Attempt to parse from string or numeric
            try:
                self.birth_date_obj = pd.to_datetime(birth_date, errors='coerce')
            except:
                pass

        # If parsing failed or the result is NaT, then fallback to "today + 1 year"
        if pd.isna(self.birth_date_obj):
            self.birth_date_obj = pd.Timestamp.now() + pd.DateOffset(years=1)

        # ---------------------------------------------------------------------
        # 2) Patron type logic
        # ---------------------------------------------------------------------
        # Calculate age in whole years (could be negative if birth_date is in the future!)
        self.years_old = int((pd.Timestamp.now() - self.birth_date_obj).days / 365)

        # Example: age-based logic
        if self.years_old >= 18:
            self.patron_type = 3
        elif self.years_old >= 13:
            self.patron_type = 2
        else:
            self.patron_type = 1

        # ---------------------------------------------------------------------
        # 3) Calculate the expiration date N years from now
        # ---------------------------------------------------------------------
        expiration_date = (
            pd.Timestamp.now() + pd.DateOffset(years=years_until_expiration)
        ).strftime('%Y-%m-%d')

        # ---------------------------------------------------------------------
        # 4) Prepare phone string (avoid crash on NaN)
        # ---------------------------------------------------------------------
        if phone_number is not None and not pd.isna(phone_number):
            phone_str = str(int(phone_number))
        else:
            phone_str = ""

        # ---------------------------------------------------------------------
        # 5) Addresses
        # ---------------------------------------------------------------------
        addresses_line1 = home_legal_address
        addresses_line2 = f"{home_legal_address_city}, {home_legal_address_state} {home_legal_address_zip}"


        # ---------------------------------------------------------------------
        # 6) Notice Preference
        # ---------------------------------------------------------------------
        if notice_pref and notice_pref in ('-', 'z', 'a', 'p'):
            self.notice_pref = notice_pref
        else:
            self.notice_pref = '-'  # no notice

        # ---------------------------------------------------------------------
        # 7) Barcode
        # ---------------------------------------------------------------------
        try:
            self.barcode = str(barcode)
        except Exception as e:
            self.barcode = ''
        
        # ---------------------------------------------------------------------
        # 7) Build the final data structure
        # ---------------------------------------------------------------------
        self.patron_data = {
            'expirationDate': expiration_date,
            'birthDate': self.birth_date_obj.strftime('%Y-%m-%d'),  # string version
            'patronType': self.patron_type,
            'blockInfo': {'code': '-'},
            'phones': [{'number': phone_str, 'type': 't'}],
            'pMessage': '-',
            'fixedFields': {
                # Examples, your codes may differ
                '44': {'label': 'E-Lib Update? (P1)', 'value': 'n'},
                '45': {'label': 'Friends? (P2)', 'value': 'n'},
                '46': {'label': 'Foundation? (P3)', 'value': '1'},
                '86': {'label': 'Agency', 'value': str(patron_agency)},
                '158': {'label': 'Patron Agency', 'value': str(patron_agency)},
                # Default to 'z' => "no notices" or "email"? Possibly read from your data 
                '268': {'label': 'Notice Preference', 'value': self.notice_pref},
            },
            "names": [
                f"{last_name}, {first_name}"
            ],
            "barcodes": [
                self.barcode
            ],
            "homeLibraryCode": str(home_library_code),
            "varFields": [
                # fieldTag "d" => “birthDate” in MMDDYYYY
                {
                    'fieldTag': 'd',
                    'content': self.birth_date_obj.strftime('%m%d%Y')
                },
                {
                    "fieldTag": 'x',
                    "content": "ConnectED"
                },
                {
                    "fieldTag": "l",
                    "content": str(school).strip().title() if school else ""
                },
            ],
            "addresses": [
                {
                    "lines": [
                        str(addresses_line1) if addresses_line1 else "",
                        str(addresses_line2) if addresses_line2 else ""
                    ],
                    "type": "a"
                },
            ],
            "pin": str(pin),
        }

        # Override notice preference if provided
        if notice_pref not in [None, 'nan', 'NaN']:
            self.patron_data['fixedFields']['268']['value'] = str(notice_pref)

        # If email is present
        if email_address not in [None, 'nan', 'NaN']:
            self.patron_data['emails'] = [str(email_address)]
        else:
            self.patron_data['emails'] = []

        # If alt_id is present
        if alt_id is not None and str(alt_id).strip().lower() not in ["nan", "none", ""]:
            self.patron_data['varFields'].append({
                "fieldTag": "v",
                "content": str(alt_id)
            })
