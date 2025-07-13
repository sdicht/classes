#!/usr/bin/env python3
"""
Fast Update Script - Only regenerates HTML files, skips image processing and file copying
Perfect for quick content updates during development
"""

import os
import shutil
import markdown
from pathlib import Path
import re
from datetime import datetime

class FastUpdater:
    def __init__(self, classes_dir="classes", output_dir="docs"):
        self.classes_dir = Path(classes_dir)
        self.output_dir = Path(output_dir)
    
    def extract_title_from_markdown(self, file_path):
        """Extract title from markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Skip YAML frontmatter
            start_index = 0
            if lines and lines[0].strip() == '---':
                for i, line in enumerate(lines[1:], 1):
                    if line.strip() == '---':
                        start_index = i + 1
                        break
            
            # Check for handout pattern first
            for line in lines[start_index:]:
                stripped = line.strip().lstrip('*').strip()  # Remove bold formatting
                if stripped.startswith('##') and 'handout' in stripped.lower():
                    if ':' in stripped:
                        return stripped.split(':', 1)[1].strip()
                    break
            
            # Look for slide title (first ### line)
            for line in lines[start_index:]:
                stripped = line.strip().lstrip('*').strip()
                if stripped.startswith('###'):
                    return stripped[3:].strip()
            
            # Fallback to filename
            return Path(file_path).stem.replace('_', ' ').replace('-', ' ').title()
            
        except Exception:
            return Path(file_path).stem.replace('_', ' ').replace('-', ' ').title()
    
    def is_marp_slide(self, file_path):
        """Check if markdown file is a Marp presentation"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(500)
                return ('theme:' in content and '---' in content) or 'marp:' in content
        except Exception:
            return False
    
    def parse_course_info(self, course_dir):
        """Parse course_info.txt file"""
        info_file = course_dir / "course_info.txt"
        course_info = {
            'title': course_dir.name.upper(),
            'times': '', 'description': 'Literature Course Materials',
            'instructor': '', 'office_hours': '', 'email': '', 'semester': '',
            'room': '', 'google_classroom_link': '', 'schedule_link': '',
            'textbook': '', 'shared_with': '', 'shares_from': '',
            'week_titles': {}
        }
        
        if info_file.exists():
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    current_key = None
                    current_value = []
                    
                    for line in f:
                        line = line.strip()
                        
                        if ':' in line:
                            potential_key = line.split(':')[0].lower().strip()
                            
                            standard_fields = [
                                'title', 'times', 'description', 'instructor', 
                                'office_hours', 'office hours', 'email', 'semester', 'room', 
                                'google_classroom_link', 'google classroom', 'google_classroom',
                                'schedule_link', 'schedule', 'textbook', 
                                'shared_with', 'shares_from'
                            ]
                            
                            if potential_key in standard_fields:
                                if current_key:
                                    course_info[current_key] = '\n'.join(current_value).strip()
                                
                                key, value = line.split(':', 1)
                                normalized_key = key.lower().replace(' ', '_')
                                if normalized_key in ['google_classroom', 'google classroom']:
                                    normalized_key = 'google_classroom_link'
                                elif normalized_key == 'schedule':
                                    normalized_key = 'schedule_link'
                                elif normalized_key == 'office hours':
                                    normalized_key = 'office_hours'
                                
                                current_key = normalized_key
                                current_value = [value.strip()] if value.strip() else []
                            else:
                                # Custom week title
                                week_title = ':'.join(line.split(':')[1:]).strip()
                                course_info['week_titles'][potential_key] = week_title
                        
                        elif current_key and line:
                            current_value.append(line)
                    
                    if current_key:
                        course_info[current_key] = '\n'.join(current_value).strip()
                        
            except Exception as e:
                print(f"⚠️ Error reading course_info.txt: {e}")
        
        return course_info
    
    def get_week_title(self, course_info, class_dir_name):
        """Get custom week title or generate from folder name"""
        if 'week_titles' in course_info and class_dir_name in course_info['week_titles']:
            return course_info['week_titles'][class_dir_name]
        else:
            return class_dir_name.replace('_', ' ').replace('-', ' ').title()
    
    def parse_links_file(self, file_path):
        """Parse links.txt file"""
        links = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '|' in line:
                        parts = line.split('|', 1)
                        if len(parts) == 2:
                            title = parts[0].strip()
                            url = parts[1].strip()
                            links.append((title, url))
        except Exception:
            pass
        return links
    
    def create_marp_viewer_fallback(self, slides_content, title, course_name, class_name):
        """Create Marp presentation viewer"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        .course-nav {{
            position: fixed; top: 0; left: 0; right: 0;
            background: rgba(48, 48, 48, 0.95); color: white;
            padding: 0.5rem 1rem; font-family: 'Lato', sans-serif;
            font-size: 0.9rem; z-index: 1000;
            border-bottom: 2px solid #70b7fd;
        }}
        .course-nav a {{
            color: #70b7fd; text-decoration: none; margin-right: 0.5rem;
        }}
        .course-nav a:hover {{ color: white; }}
        body {{ margin: 0; padding: 3rem 0 0 0; font-family: 'Lato', sans-serif; }}
    </style>
</head>
<body>
    <div class="course-nav">
        <a href="../../index.html">← All Courses</a>
        <span>/</span>
        <a href="../index.html">{course_name.upper()}</a>
        <span>/</span>
        <span>{class_name.replace('_', ' ').replace('-', ' ').title()}</span>
        <span>/</span>
        <span>{title}</span>
    </div>
    
    <div id="marp-presentation"></div>
    
    <script src="https://cdn.jsdelivr.net/npm/@marp-team/marp-core/lib/marp.min.js"></script>
    <script>
        const slideContent = `{slides_content.replace('`', '\\`').replace('${', '\\${')}`;
        const marp = new Marp({{ html: true, theme: 'gaia' }});
        const {{ html, css }} = marp.render(slideContent);
        
        const style = document.createElement('style');
        style.textContent = css;
        document.head.appendChild(style);
        
        document.getElementById('marp-presentation').innerHTML = html;
    </script>
</body>
</html>"""
    
    def create_handout_page(self, handout_content, title, course_name, class_name):
        """Create handout HTML page"""
        md = markdown.Markdown(extensions=['extra', 'codehilite', 'toc'])
        html_content = md.convert(handout_content)
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="../../styles.css">
</head>
<body>
    <div class="container">
        <div class="breadcrumb">
            <a href="../../index.html">← All Courses</a>
            <span>/</span>
            <a href="../index.html">{course_name.upper()}</a>
            <span>/</span>
            <span>{class_name.replace('_', ' ').replace('-', ' ').title()}</span>
            <span>/</span>
            <span>{title}</span>
        </div>
        
        <div class="handout-content">
            {html_content}
        </div>
    </div>
</body>
</html>"""
    
    def create_course_page(self, course_name, course_info, classes_data):
        """Create course index page"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Course info section
        info_html = ""
        if course_info:
            info_items = []
            
            if course_info.get('times'):
                info_items.append(f'<div class="info-item"><strong>Class Times:</strong> {course_info["times"]}</div>')
            if course_info.get('semester'):
                info_items.append(f'<div class="info-item"><strong>Semester:</strong> {course_info["semester"]}</div>')
            if course_info.get('room'):
                info_items.append(f'<div class="info-item"><strong>Room:</strong> {course_info["room"]}</div>')
            if course_info.get('office_hours'):
                info_items.append(f'<div class="info-item"><strong>Office Hours:</strong> {course_info["office_hours"]}</div>')
            if course_info.get('email'):
                info_items.append(f'<div class="info-item"><strong>Email:</strong> {course_info["email"]}</div>')
            if course_info.get('google_classroom_link'):
                info_items.append(f'<div class="info-item"><strong>Google Classroom:</strong> <a href="{course_info["google_classroom_link"]}" target="_blank">Access Classroom</a></div>')
            if course_info.get('schedule_link'):
                if course_info.get('schedule_file'):
                    info_items.append(f'<div class="info-item"><strong>Schedule:</strong> <a href="schedule.html">View Schedule</a></div>')
                else:
                    info_items.append(f'<div class="info-item"><strong>Schedule:</strong> <a href="{course_info["schedule_link"]}" target="_blank">View Schedule</a></div>')
            if course_info.get('textbook'):
                textbook = course_info['textbook']
                if textbook.lower().endswith('.pdf'):
                    info_items.append(f'<div class="info-item"><strong>Textbook:</strong> <a href="{textbook}" target="_blank">Download PDF</a></div>')
                elif textbook.startswith('http'):
                    info_items.append(f'<div class="info-item"><strong>Textbook:</strong> <a href="{textbook}" target="_blank">View Online</a></div>')
                else:
                    info_items.append(f'<div class="info-item"><strong>Textbook:</strong> {textbook}</div>')
            
            description_html = ""
            if course_info.get('description'):
                description_html = f'<div class="description"><strong>Course Description:</strong><br>{course_info["description"]}</div>'
            
            if info_items or description_html:
                info_html = f"""
                <div class="course-meta">
                    <h2>Course Information</h2>
                    <div class="info-grid">
                        {''.join(info_items)}
                    </div>
                    {description_html}
                </div>
                """
        
        # Classes section
        classes_html = ""
        for class_dir, materials in sorted(classes_data.items()):
            class_name = self.get_week_title(course_info, class_dir)
            
            # Group materials
            slides_html = handouts_html = pdfs_html = links_html = ""
            
            if materials.get('slides'):
                slides_html = '<div class="materials-section"><h4>Slides</h4><ul class="materials-list">'
                for slide_info in materials['slides']:
                    slides_html += f'<li><a href="{class_dir}/{slide_info["filename"]}">📊 {slide_info["title"]}</a></li>'
                slides_html += '</ul></div>'
            
            if materials.get('handouts'):
                handouts_html = '<div class="materials-section"><h4>Handouts</h4><ul class="materials-list">'
                for handout_info in materials['handouts']:
                    handouts_html += f'<li><a href="{class_dir}/{handout_info["filename"]}">📄 {handout_info["title"]}</a></li>'
                handouts_html += '</ul></div>'
            
            if materials.get('pdfs'):
                pdfs_html = '<div class="materials-section"><h4>Documents</h4><ul class="materials-list">'
                for pdf_name in sorted(materials['pdfs']):
                    pdfs_html += f'<li><a href="{class_dir}/{pdf_name}" target="_blank">📎 {pdf_name}</a></li>'
                pdfs_html += '</ul></div>'
            
            if materials.get('links'):
                links_html = '<div class="materials-section"><h4>External Links</h4><ul class="materials-list">'
                for link_title, link_url in materials['links']:
                    links_html += f'<li><a href="{link_url}" target="_blank">🔗 {link_title}</a></li>'
                links_html += '</ul></div>'
            
            all_materials = slides_html + handouts_html + pdfs_html + links_html
            
            if all_materials:
                classes_html += f"""
                <div class="class-card">
                    <h3>{class_name}</h3>
                    {all_materials}
                </div>
                """
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{course_info.get('title', course_name.upper())} - Literature Course</title>
    <link rel="stylesheet" href="../styles.css">
</head>
<body>
    <div class="container">
        <div class="breadcrumb">
            <a href="../index.html">← All Courses</a>
            <span>/</span>
            <span>{course_info.get('title', course_name.upper())}</span>
        </div>
        
        <header>
            <h1>{course_info.get('title', course_name.upper())}</h1>
        </header>
        
        {info_html}
        
        <h2>Class Materials</h2>
        <div class="course-grid">
            {classes_html}
        </div>
        
        <div class="last-updated">
            Last updated: {current_time}
        </div>
    </div>
</body>
</html>"""
    
    def create_main_index(self, courses_info, instructor_name="Pedro Groppo"):
        """Create main index page"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        courses_html = ""
        for course_name, course_info in sorted(courses_info.items()):
            course_title = course_info.get('title', course_name.upper())
            description = course_info.get('description', 'Literature Course Materials')
            times = course_info.get('times', '')
            semester = course_info.get('semester', '')
            room = course_info.get('room', '')
            
            preview_info = []
            if semester: preview_info.append(f"📅 {semester}")
            if times: preview_info.append(f"⏰ {times}")
            if room: preview_info.append(f"📍 {room}")
            
            preview_text = "<br>".join(preview_info) if preview_info else ""
            
            courses_html += f"""
            <div class="course-card">
                <a href="{course_name}/index.html">
                    <h3>{course_title}</h3>
                    <p>{description}</p>
                    {f'<div class="course-preview">{preview_text}</div>' if preview_text else ''}
                </a>
            </div>
            """
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Literature Courses - {instructor_name}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Course Materials</h1>
            <p style="text-align: center; color: #606060; font-size: 1.2rem; margin-bottom: 0.5rem;">
                {instructor_name}
            </p>
            <p style="text-align: center; color: #606060; font-size: 1rem;">
                Select a course to view materials
            </p>
        </header>
        
        <div class="course-grid">
            {courses_html}
        </div>
        
        <div class="last-updated">
            Last updated: {current_time}
        </div>
    </div>
</body>
</html>"""
    
    def fast_update(self):
        """Fast update - only regenerate HTML files"""
        print(f"⚡ Fast update: regenerating HTML files only...")
        
        if not self.classes_dir.exists():
            print(f"❌ Classes directory not found: {self.classes_dir}")
            return
        
        if not self.output_dir.exists():
            print(f"❌ Output directory not found: {self.output_dir}")
            print("Run the full generator first to create the initial site.")
            return
        
        # Remove only HTML files
        for html_file in self.output_dir.rglob("*.html"):
            html_file.unlink()
        print("🗑️ Cleared existing HTML files")
        
        courses_info = {}
        updated_courses = 0
        
        # Process each course
        for course_dir in self.classes_dir.iterdir():
            if course_dir.is_dir():
                course_name = course_dir.name
                print(f"📚 {course_name.upper()}")
                
                course_info = self.parse_course_info(course_dir)
                courses_info[course_name] = course_info
                
                course_output_dir = self.output_dir / course_name
                course_output_dir.mkdir(exist_ok=True)
                
                classes_data = {}
                
                # Process class directories
                for class_dir in course_dir.iterdir():
                    if class_dir.is_dir() and class_dir.name != "images":
                        class_name = class_dir.name
                        class_output_dir = course_output_dir / class_name
                        class_output_dir.mkdir(exist_ok=True)
                        
                        materials = {'slides': [], 'handouts': [], 'pdfs': [], 'links': []}
                        
                        # Process markdown files
                        for md_file in class_dir.glob("*.md"):
                            title = self.extract_title_from_markdown(md_file)
                            output_filename = f"{md_file.stem}.html"
                            
                            if self.is_marp_slide(md_file):
                                # Slide
                                with open(md_file, 'r', encoding='utf-8') as f:
                                    slides_content = f.read()
                                
                                slides_html = self.create_marp_viewer_fallback(
                                    slides_content, title, course_name, class_name
                                )
                                with open(class_output_dir / output_filename, 'w', encoding='utf-8') as f:
                                    f.write(slides_html)
                                
                                materials['slides'].append({'title': title, 'filename': output_filename})
                                print(f"  📊 {title}")
                            else:
                                # Handout
                                with open(md_file, 'r', encoding='utf-8') as f:
                                    handout_content = f.read()
                                
                                handout_html = self.create_handout_page(
                                    handout_content, title, course_name, class_name
                                )
                                with open(class_output_dir / output_filename, 'w', encoding='utf-8') as f:
                                    f.write(handout_html)
                                
                                materials['handouts'].append({'title': title, 'filename': output_filename})
                                print(f"  📄 {title}")
                        
                        # Check for PDFs (just list them, don't copy)
                        pdf_files = list(class_dir.glob("*.pdf"))
                        if pdf_files:
                            materials['pdfs'] = [pdf.name for pdf in pdf_files]
                            for pdf in pdf_files:
                                print(f"  📎 {pdf.name}")
                        
                        # Process links
                        links_file = class_dir / "links.txt"
                        if links_file.exists():
                            links = self.parse_links_file(links_file)
                            if links:
                                materials['links'] = links
                                for title, url in links:
                                    print(f"  🔗 {title}")
                        
                        if any(materials.values()):
                            classes_data[class_name] = materials
                
                # Create course page
                course_html = self.create_course_page(course_name, course_info, classes_data)
                with open(course_output_dir / "index.html", 'w', encoding='utf-8') as f:
                    f.write(course_html)
                
                updated_courses += 1
        
        # Create main index
        main_html = self.create_main_index(courses_info)
        with open(self.output_dir / "index.html", 'w', encoding='utf-8') as f:
            f.write(main_html)
        
        print(f"\n⚡ Fast update complete!")
        print(f"📊 Updated {updated_courses} courses")
        print(f"🌐 Open {self.output_dir}/index.html to view")

def main():
    updater = FastUpdater()
    updater.fast_update()

if __name__ == "__main__":
    main()