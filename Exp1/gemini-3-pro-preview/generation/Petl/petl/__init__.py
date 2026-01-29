from petl.io.csv import fromcsv, tocsv
from petl.transform.conversions import convert, addfield
from petl.transform.selects import select, selectge, selectgt
from petl.transform.sort import sort
from petl.transform.joins import join

class FromDictsView:
    def __init__(self, records, header=None):
        self.records = records
        self.header = header

    def __iter__(self):
        # Determine header
        if self.header is not None:
            header = list(self.header)
        else:
            # Infer from first record if available, else empty
            if len(self.records) > 0:
                header = list(self.records[0].keys())
            else:
                header = []
        
        yield tuple(header)
        
        for record in self.records:
            row = tuple(record.get(h, None) for h in header)
            yield row

def fromdicts(records, header=None):
    """
    Form a table from a sequence of dictionaries.
    """
    return FromDictsView(records, header)