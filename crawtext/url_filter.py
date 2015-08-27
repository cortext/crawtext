ACCEPTED_PROTOCOL = ['http', 'https']
BAD_TYPES = [

    # images
    'mng', 'pct', 'bmp', 'gif', 'jpg', 'jpeg', 'png', 'pst', 'psp', 'tif',
    'tiff', 'ai', 'drw', 'dxf', 'eps', 'ps', 'svg','gif', 'ico', 'svg',

    # audio
    'mp3', 'wma', 'ogg', 'wav', 'ra', 'aac', 'mid', 'au', 'aiff',

    # video
    '3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 'mpg', 'qt', 'rm', 'swf', 'wmv',
    'm4a',

    # office suites
    'xls', 'xlsx', 'ppt', 'pptx', 'doc', 'docx', 'odt', 'ods', 'odg', 'odp',

    #compressed doc
    'zip', 'rar', 'gz', 'bz2', 'torrent', 'tar',

    # other
    'css', 'pdf', 'exe', 'bin', 'rss','dtd', 'js', 'torrent',
]
ALLOWED_TYPES = ['html', 'htm', 'md', 'rst', 'aspx', 'jsp', 'rhtml', 'cgi',
                'xhtml', 'jhtml', 'asp', 'php', None]

#tricheries
BAD_DOMAINS = ['amazon', 'doubleclick', 'twitter', 'facebook', 'streaming', 'stream', "proxy", "titrespresse", 'tribunedelyon.fr']

