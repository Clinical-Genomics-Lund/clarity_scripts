import os, time, datetime 
from data_to_pdf import DataToPdf

data = []
for path, subdirs, files in os.walk(r'/opt/gls/clarity/customextensions'):
    for filename in files:
        filepath = os.path.join(path, filename)
        filesize = os.path.getsize(filepath) / 1024

    if filesize > 1024:
        mtime = os.path.getmtime(filepath)
        mtime = datetime.datetime.strptime(time.ctime(mtime),
                                           '%a %b %d %H:%M:%S %Y')
        data.append({'filename': filename,
                     'filepath': filepath,
                     'size': filesize,
                     'mtime': mtime})
        
fields = (
    ('filename', 'Filename'),
    ('filepath', 'Filepath'),
    ('size', 'Size (KB)'),
    ('mtime', 'Modified'),
    )

doc = DataToPdf(fields, data, sort_by=('size', 'DESC'),
                title='Log Files Over 1MB')
doc.export('LogFiles.pdf')
