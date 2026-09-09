import os
import glob
import re

template_dir = 'templates'
search_str = '<li><a href="{{url_for(\'analyze_case\')}}"><i class="fas fa-microchip"></i> FIR Threat Assessment HUD</a></li>'
search_str2 = '<li><a href="{{url_for(\'analyze_case\')}}" class="active" style="color:#06b6d4;font-weight:700;"><i class="fas fa-microchip"></i> FIR Threat Assessment HUD</a></li>'

for filepath in glob.glob(os.path.join(template_dir, '*.html')):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'cdr_page' not in content:
        if search_str in content:
            replacement = search_str + '\n            <li><a href="{{url_for(\'cdr_page\')}}"><i class="fas fa-phone-volume"></i> CDR Intelligence</a></li>'
            content = content.replace(search_str, replacement)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Updated {filepath}')
        elif search_str2 in content:
            replacement = search_str2 + '\n            <li><a href="{{url_for(\'cdr_page\')}}"><i class="fas fa-phone-volume"></i> CDR Intelligence</a></li>'
            content = content.replace(search_str2, replacement)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Updated {filepath}')
