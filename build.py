#!/usr/bin/env python3
"""
Enhanced Literature Course Website Generator with Simple Material Sharing
- Simple sharing: courses can share materials by specifying shares_from: course_name
- Multiple slides and handouts per class
- Clean Marp presentation mode (no frames)
- Marp-CLI integration with fallback
- Course info from txt files with Room, Google Classroom, Schedule links
- Image compression with PIL
- Custom week titles (e.g., hardy: Thomas Hardy)
- Schedule MD table viewer
- Enhanced handout styling
"""

import os
import shutil
import markdown
from pathlib import Path
import re
import subprocess
import tempfile
from datetime import datetime
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class LiteratureCourseGenerator:
    def __init__(self, classes_dir="classes", output_dir="docs"):
        self.classes_dir = Path(classes_dir)
        self.output_dir = Path(output_dir)
        
        if not PIL_AVAILABLE:
            print("⚠️  Warning: PIL (Pillow) not installed. Image compression disabled.")
            print("   Install with: pip install Pillow")
        
        # Check for marp-cli
        self.marp_cli_available = self.check_marp_cli()
    
    def check_marp_cli(self):
        """Check if marp-cli is available"""
        try:
            result = subprocess.run(['marp', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Marp CLI found: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        print("⚠️  Marp CLI not found. Using browser-based Marp rendering.")
        print("   Install with: npm install -g @marp-team/marp-cli")
        return False
    
    def is_marp_slide(self, file_path):
        """Check if markdown file is a Marp presentation"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(500)  # Check first 500 chars
                # Look for Marp frontmatter or theme directive
                return ('theme:' in content and '---' in content) or 'marp:' in content
        except Exception:
            return False
    
    def extract_title_from_markdown(self, file_path):
        """
        Extract title from markdown file:
        - For slides: first line starting with '###' after YAML frontmatter
        - For handouts: content after ':' in line starting with '##' containing 'handout'
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Skip YAML frontmatter if present
            start_index = 0
            if lines and lines[0].strip() == '---':
                for i, line in enumerate(lines[1:], 1):
                    if line.strip() == '---':
                        start_index = i + 1
                        break
            
            # Check if it's a handout first
            for line in lines[start_index:]:
                stripped = line.strip()
                if stripped.startswith('##') and 'handout' in stripped.lower():
                    if ':' in stripped:
                        return stripped.split(':', 1)[1].strip()
                    break
            
            # If not handout, look for slide title (first ### line)
            for line in lines[start_index:]:
                stripped = line.strip()
                if stripped.startswith('###'):
                    return stripped[3:].strip()
            
            # Fallback to filename
            return Path(file_path).stem.replace('_', ' ').replace('-', ' ').title()
            
        except Exception as e:
            print(f"Error extracting title from {file_path}: {e}")
            return Path(file_path).stem.replace('_', ' ').replace('-', ' ').title()
    
    def get_markdown_files(self, class_dir):
        """Get all markdown files and categorize them"""
        slides = []
        handouts = []
        
        for md_file in class_dir.glob("*.md"):
            if self.is_marp_slide(md_file):
                slides.append(md_file)
            else:
                handouts.append(md_file)
        
        return sorted(slides), sorted(handouts)
    
    def convert_marp_with_cli(self, input_file, output_file):
        """Convert Marp markdown to HTML using marp-cli"""
        if not self.marp_cli_available:
            return False
        
        try:
            # Use marp-cli to convert to HTML
            cmd = [
                'marp',
                str(input_file),
                '--html',
                '--output', str(output_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True
            else:
                print(f"    ⚠️  Marp CLI error for {input_file.name}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"    ❌ Error running marp-cli for {input_file.name}: {e}")
            return False
    
    def enhance_marp_html(self, html_file, title, course_name, class_name):
        """Enhanced Marp HTML with mobile-friendly fullscreen and navigation"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Mobile-optimized navigation and fullscreen controls
            mobile_enhancements = """
            <style>
                /* Mobile-first navigation */
                .course-nav {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    background: rgba(48, 48, 48, 0.95);
                    color: white;
                    padding: 0.5rem 1rem;
                    font-family: 'Lato', sans-serif;
                    font-size: 0.9rem;
                    z-index: 1000;
                    border-bottom: 2px solid #70b7fd;
                    transition: transform 0.3s ease;
                }
                
                /* Hide navigation in fullscreen mode */
                .course-nav.hidden {
                    transform: translateY(-100%);
                }
                
                .course-nav a {
                    color: #70b7fd;
                    text-decoration: none;
                    margin-right: 0.5rem;
                }
                
                .course-nav a:hover {
                    color: white;
                }
                
                /* Mobile fullscreen button */
                .mobile-controls {
                    position: fixed;
                    top: 4rem;
                    right: 1rem;
                    z-index: 1001;
                    display: flex;
                    gap: 0.5rem;
                }
                
                .control-btn {
                    background: rgba(48, 48, 48, 0.9);
                    color: white;
                    border: none;
                    padding: 0.75rem;
                    border-radius: 50%;
                    font-size: 1.2rem;
                    cursor: pointer;
                    width: 50px;
                    height: 50px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.3s ease;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                }
                
                .control-btn:hover, .control-btn:active {
                    background: #70b7fd;
                    transform: scale(1.1);
                }
                
                /* Hide controls in fullscreen */
                .mobile-controls.hidden {
                    opacity: 0;
                    pointer-events: none;
                }
                
                /* Marp container adjustments */
                body {
                    padding-top: 3rem;
                    transition: padding 0.3s ease;
                }
                
                body.fullscreen-mode {
                    padding-top: 0;
                }
                
                /* Mobile landscape optimizations */
                @media screen and (orientation: landscape) and (max-width: 1024px) {
                    .course-nav {
                        padding: 0.25rem 0.5rem;
                        font-size: 0.8rem;
                    }
                    
                    body {
                        padding-top: 2.5rem;
                    }
                    
                    .mobile-controls {
                        top: 3rem;
                        right: 0.5rem;
                    }
                    
                    .control-btn {
                        width: 40px;
                        height: 40px;
                        font-size: 1rem;
                    }
                }
                
                /* iOS Safari specific fixes */
                @supports (-webkit-touch-callout: none) {
                    /* Fix for iOS viewport issues */
                    body {
                        -webkit-overflow-scrolling: touch;
                    }
                    
                    /* Prevent zoom on double tap */
                    * {
                        touch-action: manipulation;
                    }
                    
                    /* iOS fullscreen improvements */
                    body.fullscreen-mode {
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        overflow: hidden;
                    }
                }
                
                /* Android Chrome specific fixes */
                @media screen and (-webkit-min-device-pixel-ratio: 0) {
                    .course-nav {
                        -webkit-backdrop-filter: blur(10px);
                        backdrop-filter: blur(10px);
                    }
                }
                
                /* Hide Marp's built-in fullscreen for mobile */
                @media (max-width: 768px) {
                    [data-marp-presenter] {
                        display: none !important;
                    }
                }
            </style>
            
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="apple-mobile-web-app-capable" content="yes">
            <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
            <meta name="mobile-web-app-capable" content="yes">
            """
            
            navigation_bar = f"""
            <div class="course-nav" id="courseNav">
                <a href="../../index.html">← All Courses</a>
                <span>/</span>
                <a href="../index.html">{course_name.upper()}</a>
                <span>/</span>
                <span>{class_name.replace('_', ' ').replace('-', ' ').title()}</span>
                <span>/</span>
                <span>{title}</span>
            </div>
            
            <div class="mobile-controls" id="mobileControls">
                <button class="control-btn" onclick="toggleFullscreen()" title="Toggle Fullscreen">
                    📱
                </button>
                <button class="control-btn" onclick="toggleNavigation()" title="Toggle Navigation">
                    🧭
                </button>
            </div>
            """
            
            # JavaScript for mobile enhancements
            mobile_script = """
            <script>
                let isFullscreen = false;
                let isNavHidden = false;
                
                function toggleFullscreen() {
                    const body = document.body;
                    const nav = document.getElementById('courseNav');
                    const controls = document.getElementById('mobileControls');
                    
                    if (!isFullscreen) {
                        // Enter fullscreen mode
                        if (document.documentElement.requestFullscreen) {
                            document.documentElement.requestFullscreen();
                        } else if (document.documentElement.webkitRequestFullscreen) {
                            document.documentElement.webkitRequestFullscreen();
                        } else if (document.documentElement.msRequestFullscreen) {
                            document.documentElement.msRequestFullscreen();
                        }
                        
                        body.classList.add('fullscreen-mode');
                        nav.classList.add('hidden');
                        controls.classList.add('hidden');
                        isFullscreen = true;
                    } else {
                        // Exit fullscreen mode
                        if (document.exitFullscreen) {
                            document.exitFullscreen();
                        } else if (document.webkitExitFullscreen) {
                            document.webkitExitFullscreen();
                        } else if (document.msExitFullscreen) {
                            document.msExitFullscreen();
                        }
                        
                        body.classList.remove('fullscreen-mode');
                        if (!isNavHidden) {
                            nav.classList.remove('hidden');
                        }
                        controls.classList.remove('hidden');
                        isFullscreen = false;
                    }
                }
                
                function toggleNavigation() {
                    const nav = document.getElementById('courseNav');
                    
                    if (!isFullscreen) {
                        if (isNavHidden) {
                            nav.classList.remove('hidden');
                            isNavHidden = false;
                        } else {
                            nav.classList.add('hidden');
                            isNavHidden = true;
                        }
                    }
                }
                
                // Handle fullscreen change events
                document.addEventListener('fullscreenchange', handleFullscreenChange);
                document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
                document.addEventListener('msfullscreenchange', handleFullscreenChange);
                
                function handleFullscreenChange() {
                    const isCurrentlyFullscreen = !!(document.fullscreenElement || 
                        document.webkitFullscreenElement || 
                        document.msFullscreenElement);
                    
                    if (!isCurrentlyFullscreen && isFullscreen) {
                        // User exited fullscreen via browser controls
                        toggleFullscreen();
                    }
                }
                
                // Mobile orientation change handling
                window.addEventListener('orientationchange', function() {
                    setTimeout(function() {
                        // Force layout recalculation after orientation change
                        const marpContainer = document.querySelector('[data-marp-presentation]');
                        if (marpContainer) {
                            marpContainer.style.display = 'none';
                            marpContainer.offsetHeight; // Trigger reflow
                            marpContainer.style.display = '';
                        }
                    }, 100);
                });
                
                // Touch gesture handling for navigation
                let touchStartY = 0;
                let touchEndY = 0;
                
                document.addEventListener('touchstart', function(e) {
                    touchStartY = e.changedTouches[0].screenY;
                });
                
                document.addEventListener('touchend', function(e) {
                    touchEndY = e.changedTouches[0].screenY;
                    handleSwipe();
                });
                
                function handleSwipe() {
                    const swipeThreshold = 50;
                    const diff = touchStartY - touchEndY;
                    
                    if (Math.abs(diff) > swipeThreshold) {
                        if (diff > 0) {
                            // Swipe up - hide navigation
                            if (!isFullscreen && !isNavHidden) {
                                toggleNavigation();
                            }
                        } else {
                            // Swipe down - show navigation
                            if (!isFullscreen && isNavHidden) {
                                toggleNavigation();
                            }
                        }
                    }
                }
                
                // Prevent default touch behaviors that interfere with presentation
                document.addEventListener('touchmove', function(e) {
                    if (isFullscreen) {
                        e.preventDefault();
                    }
                }, { passive: false });
                
                // Auto-hide navigation after delay on mobile
                let hideTimer;
                function resetHideTimer() {
                    clearTimeout(hideTimer);
                    if (window.innerWidth <= 768 && !isNavHidden && !isFullscreen) {
                        hideTimer = setTimeout(function() {
                            toggleNavigation();
                        }, 5000); // Hide after 5 seconds of inactivity
                    }
                }
                
                document.addEventListener('touchstart', resetHideTimer);
                document.addEventListener('mousemove', resetHideTimer);
                
                // Initialize on load
                window.addEventListener('load', function() {
                    if (window.innerWidth <= 768) {
                        resetHideTimer();
                    }
                });
            </script>
            """
            
            # Insert enhancements into the head
            head_end = content.find('</head>')
            if head_end != -1:
                enhanced_content = (content[:head_end] + 
                                mobile_enhancements + 
                                '</head>' + 
                                content[head_end + 7:])
            else:
                enhanced_content = content
            
            # Insert navigation and controls after body tag
            body_start = enhanced_content.find('<body')
            if body_start != -1:
                body_tag_end = enhanced_content.find('>', body_start) + 1
                enhanced_content = (enhanced_content[:body_tag_end] + 
                                navigation_bar + 
                                enhanced_content[body_tag_end:])
            
            # Insert script before closing body tag
            body_end = enhanced_content.rfind('</body>')
            if body_end != -1:
                enhanced_content = (enhanced_content[:body_end] + 
                                mobile_script + 
                                enhanced_content[body_end:])
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(enhanced_content)
            
            return True
            
        except Exception as e:
            print(f"    ❌ Error enhancing HTML for {html_file}: {e}")
            return False
    
    def create_marp_viewer_fallback(self, slides_content, title, course_name, class_name):
        """Clean Marp presentation without container frames"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        .course-nav {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(48, 48, 48, 0.95);
            color: white;
            padding: 0.5rem 1rem;
            font-family: 'Lato', sans-serif;
            font-size: 0.9rem;
            z-index: 1000;
            border-bottom: 2px solid #70b7fd;
        }}
        .course-nav a {{
            color: #70b7fd;
            text-decoration: none;
            margin-right: 0.5rem;
        }}
        .course-nav a:hover {{
            color: white;
        }}
        body {{
            margin: 0;
            padding: 3rem 0 0 0;
            font-family: 'Lato', sans-serif;
        }}
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
    
    <script src="https://unpkg.com/@marp-team/marp-core/lib/marp.min.js"></script>
    <script>
        const slideContent = `{slides_content.replace('`', '\\`').replace('${', '\\${')}`;
        const marp = new Marp({{
            html: true,
            theme: 'gaia'
        }});
        
        const {{ html, css }} = marp.render(slideContent);
        
        const style = document.createElement('style');
        style.textContent = css;
        document.head.appendChild(style);
        
        const container = document.getElementById('marp-presentation');
        container.innerHTML = html;
    </script>
</body>
</html>"""
    
    def create_handout_page(self, handout_content, title, course_name, class_name):
        """Create handout HTML page with enhanced styling"""
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
    
    def create_schedule_page(self, schedule_content, course_name, course_info):
        """Create schedule HTML page from markdown table"""
        md = markdown.Markdown(extensions=['tables', 'extra'])
        html_content = md.convert(schedule_content)
        
        course_title = course_info.get('title', course_name.upper())
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Schedule - {course_title}</title>
    <link rel="stylesheet" href="../styles.css">
    <style>
        .schedule-content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 2rem 0;
        }}
        .schedule-content th,
        .schedule-content td {{
            border: 1px solid #d6d6d6;
            padding: 0.75rem;
            text-align: left;
            vertical-align: top;
        }}
        .schedule-content th {{
            background-color: #70b7fd;
            color: white;
            font-weight: 600;
        }}
        .schedule-content tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .schedule-content tr:hover {{
            background-color: #f0f8ff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="breadcrumb">
            <a href="../index.html">← All Courses</a>
            <span>/</span>
            <a href="index.html">{course_title}</a>
            <span>/</span>
            <span>Schedule</span>
        </div>
        
        <header>
            <h1>Course Schedule</h1>
        </header>
        
        <div class="schedule-content">
            {html_content}
        </div>
    </div>
</body>
</html>"""
    
    def parse_course_info(self, course_dir):
        """Parse course_info.txt file for course metadata including sharing relationships"""
        info_file = course_dir / "course_info.txt"
        course_info = {
            'title': course_dir.name.upper(),
            'times': '',
            'description': 'Literature Course Materials',
            'instructor': '',
            'office_hours': '',
            'email': '',
            'semester': '',
            'room': '',
            'google_classroom_link': '',
            'schedule_link': '',
            'textbook': '',
            'shared_with': '',      # Other courses this course shares with
            'shares_from': '',      # Course this one gets materials from
            'week_titles': {}
        }
        
        if info_file.exists():
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    current_key = None
                    current_value = []
                    
                    for line in f:
                        line = line.strip()
                        
                        # Check for week title entries or standard fields
                        if ':' in line:
                            potential_key = line.split(':')[0].lower().strip()
                            
                            # Standard course info fields (including sharing fields)
                            standard_fields = [
                                'title', 'times', 'description', 'instructor', 
                                'office_hours', 'office hours', 'email', 'semester', 'room', 
                                'google_classroom_link', 'google classroom', 'google_classroom',
                                'schedule_link', 'schedule', 'textbook', 
                                'shared_with', 'shares_from'  # NEW sharing fields
                            ]
                            
                            if potential_key in standard_fields:
                                # Handle regular course info fields
                                if current_key:
                                    course_info[current_key] = '\n'.join(current_value).strip()
                                
                                key, value = line.split(':', 1)
                                # Normalize field names
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
                                # Treat as custom week title
                                week_title = ':'.join(line.split(':')[1:]).strip()
                                course_info['week_titles'][potential_key] = week_title
                        
                        elif current_key and line:
                            current_value.append(line)
                    
                    if current_key:
                        course_info[current_key] = '\n'.join(current_value).strip()
                        
                week_count = len(course_info['week_titles'])
                print(f"    📋 Loaded course info: {course_info['title']}")
                if week_count > 0:
                    print(f"    📅 Found {week_count} custom week titles")
                
                # Log sharing relationships
                if course_info.get('shared_with'):
                    print(f"    🔗 Shares materials with: {course_info['shared_with']}")
                if course_info.get('shares_from'):
                    print(f"    📚 Uses materials from: {course_info['shares_from']}")
                    
                # Check for schedule file if schedule_link is specified
                if course_info.get('schedule_link'):
                    schedule_file = course_dir / course_info['schedule_link']
                    if schedule_file.exists() and schedule_file.suffix.lower() == '.md':
                        course_info['schedule_file'] = schedule_file
                        print(f"    📅 Found schedule file: {course_info['schedule_link']}")
                    
            except Exception as e:
                print(f"    ⚠️  Error reading course_info.txt: {e}")
        
        return course_info
    
    def get_materials_source(self, course_name, course_info):
        """Determine where to get materials from - either the course itself or a shared source"""
        if course_info.get('shares_from'):
            source_course = course_info['shares_from']
            source_dir = self.classes_dir / source_course
            
            if source_dir.exists():
                print(f"    📚 Using materials from: {source_course}")
                return source_dir, source_course
            else:
                print(f"    ⚠️  Source course '{source_course}' not found, using own materials")
                return self.classes_dir / course_name, course_name
        else:
            return self.classes_dir / course_name, course_name
    
    def get_week_title(self, course_info, class_dir_name):
        """Get custom week title or generate from folder name"""
        if 'week_titles' in course_info and class_dir_name in course_info['week_titles']:
            return course_info['week_titles'][class_dir_name]
        else:
            # Fallback to formatted folder name
            return class_dir_name.replace('_', ' ').replace('-', ' ').title()
    
    def compress_and_copy_images(self, source_images_dir, course_output_dir, max_width=1200, quality=75):
        """Compress images from /images and copy to course images folder"""
        if not PIL_AVAILABLE or not source_images_dir.exists():
            return
            
        output_images_dir = course_output_dir / "images"
        output_images_dir.mkdir(exist_ok=True)
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
        compressed_count = 0
        
        for image_file in source_images_dir.iterdir():
            if image_file.suffix.lower() in image_extensions:
                try:
                    with Image.open(image_file) as img:
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        
                        if img.width > max_width:
                            ratio = max_width / img.width
                            new_height = int(img.height * ratio)
                            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                        
                        output_path = output_images_dir / image_file.name
                        if image_file.suffix.lower() in {'.jpg', '.jpeg'}:
                            img.save(output_path, 'JPEG', quality=quality, optimize=True)
                        elif image_file.suffix.lower() == '.png':
                            img.save(output_path, 'PNG', optimize=True)
                        else:
                            img.save(output_path, quality=quality, optimize=True)
                        
                        compressed_count += 1
                        
                        original_size = image_file.stat().st_size
                        compressed_size = output_path.stat().st_size
                        reduction = (1 - compressed_size/original_size) * 100
                        print(f"    🖼️  {image_file.name}: {original_size//1024}KB → {compressed_size//1024}KB ({reduction:.1f}% reduction)")
                        
                except Exception as e:
                    print(f"    ❌ Error compressing {image_file.name}: {e}")
                    try:
                        shutil.copy2(image_file, output_images_dir / image_file.name)
                        print(f"    📋 Copied original: {image_file.name}")
                    except Exception:
                        pass
        
        if compressed_count > 0:
            print(f"    ✅ Compressed {compressed_count} images")
    
    def copy_class_images(self, class_dir, class_output_dir):
        """Copy images from individual class folder to output"""
        class_images_dir = class_dir / "images"
        if not class_images_dir.exists():
            return
        
        output_images_dir = class_output_dir / "images"
        output_images_dir.mkdir(exist_ok=True)
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif', '.svg'}
        copied_count = 0
        
        for image_file in class_images_dir.iterdir():
            if image_file.suffix.lower() in image_extensions:
                try:
                    shutil.copy2(image_file, output_images_dir / image_file.name)
                    copied_count += 1
                    print(f"    🖼️  Class image: {image_file.name}")
                except Exception as e:
                    print(f"    ❌ Error copying class image {image_file.name}: {e}")
        
        if copied_count > 0:
            print(f"    ✅ Copied {copied_count} class-specific images")
    
    def parse_links_file(self, file_path):
        """Parse links.txt file with format 'Title | URL'"""
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
        except Exception as e:
            print(f"Error parsing links file {file_path}: {e}")
        return links
    
    def get_all_pdfs(self, class_dir):
        """Get all PDF files in the class directory"""
        try:
            return list(class_dir.glob("*.pdf"))
        except Exception as e:
            print(f"Error getting PDFs from {class_dir}: {e}")
            return []
    
    def create_css_file(self):
        """Create separate CSS file with enhanced styling and improved code blocks"""
        css_content = """
        /* Literature Course Website - Enhanced Multi-Material Styling */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Lato', 'Avenir Next', 'Avenir', 'Trebuchet MS', 'Segoe UI', sans-serif;
            line-height: 1.6;
            color: #303030;
            background-color: #fafafa;
            font-size: 16px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        header {
            background: #ffffff;
            border-bottom: 3px solid #70b7fd;
            padding: 2rem 0;
            margin-bottom: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .course-meta {
            background: #ffffff;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 2rem;
            border-left: 4px solid #70b7fd;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .course-meta h2 {
            color: #303030;
            margin-bottom: 1rem;
            border-bottom: none;
            font-size: 1.5rem;
        }
        
        .course-meta .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .course-meta .info-item {
            background: #fafafa;
            padding: 1rem;
            border-radius: 4px;
            border: 1px solid #d6d6d6;
        }
        
        .course-meta .info-item strong {
            color: #70b7fd;
            display: block;
            margin-bottom: 0.5rem;
        }
        
        .course-meta .info-item a {
            color: #303030;
            text-decoration: none;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            transition: all 0.2s ease;
            display: inline-block;
            background: #e8f4fd;
            border: 1px solid #70b7fd;
        }
        
        .course-meta .info-item a:hover {
            background: #70b7fd;
            color: white;
        }
        
        .course-meta .description {
            grid-column: 1 / -1;
            background: #fafafa;
            padding: 1rem;
            border-radius: 4px;
            border: 1px solid #d6d6d6;
            margin-top: 1rem;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #303030;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        
        h1 {
            font-size: 2.5rem;
            text-align: center;
            font-weight: 300;
            letter-spacing: -0.02em;
        }
        
        h2 {
            font-size: 2rem;
            border-bottom: 2px solid #70b7fd;
            padding-bottom: 0.5rem;
            margin-top: 2rem;
        }
        
        .course-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        
        .course-card, .class-card {
            background: #ffffff;
            border: 1px solid #d6d6d6;
            border-radius: 8px;
            padding: 2rem;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .course-card:hover, .class-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            border-color: #70b7fd;
        }
        
        .course-card h3, .class-card h3 {
            color: #303030;
            margin-bottom: 1rem;
            font-size: 1.4rem;
        }
        
        .course-card a, .class-card a {
            text-decoration: none;
            color: inherit;
            display: block;
        }
        
        .course-card .course-preview {
            color: #606060;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        
        .materials-list {
            list-style: none;
            margin-top: 1rem;
        }
        
        .materials-list li {
            margin-bottom: 0.5rem;
            padding-left: 1.5rem;
            position: relative;
        }
        
        .materials-list li:before {
            content: "→";
            position: absolute;
            left: 0;
            color: #70b7fd;
            font-weight: bold;
        }
        
        .materials-list a {
            color: #303030;
            text-decoration: none;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            transition: all 0.2s ease;
        }
        
        .materials-list a:hover {
            background-color: #70b7fd;
            color: white;
        }
        
        /* Material type grouping */
        .materials-section {
            margin-bottom: 1.5rem;
        }
        
        .materials-section h4 {
            color: #70b7fd;
            font-size: 1rem;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .breadcrumb {
            background: #ffffff;
            padding: 1rem 0;
            margin-bottom: 3rem;
            border-left: 4px solid #70b7fd;
            padding-left: 1rem;
        }
        
        .breadcrumb a {
            color: #606060;
            text-decoration: none;
            margin-right: 0.5rem;
        }
        
        .breadcrumb a:hover {
            color: #70b7fd;
        }
        
        .breadcrumb span {
            color: #606060;
            margin: 0 0.5rem;
        }
        
        .handout-content, .schedule-content {
            background: #ffffff;
            padding: 2rem;
            border-radius: 8px;
            margin: 2rem 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .handout-content h1, .handout-content h2, .handout-content h3 {
            color: #303030;
        }
        
        .handout-content p {
            margin-bottom: 1rem;
            line-height: 1.8;
        }
        
        .handout-content ul, .handout-content ol {
            margin-left: 2rem;
            margin-bottom: 1rem;
        }
        
        .handout-content blockquote {
            border-left: 4px solid #70b7fd;
            margin: 1rem 0;
            padding-left: 1rem;
            font-style: italic;
            color: #606060;
        }

        .handout-content hr {
            margin: 2.5rem 0;          /* More space above and below */
            border: none;
            border-top: 2px solid #d6d6d6;
            background: none;
            opacity: 0.6;
        }

        .handout-content hr + * {
            margin-top: 0;             /* Remove extra margin from element after hr */
        }

        .handout-content * + hr {
            margin-top: 2.5rem;        /* Ensure space before hr */
        }
        
        /* Enhanced code block styling */
        .handout-content pre {
            background: #f8f8f8;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 1.5rem;
            margin: 2rem 0;
            overflow-x: auto;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9rem;
            line-height: 1.4;
        }
        
        .handout-content code {
            background: #f0f0f0;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
        }
        
        .handout-content pre code {
            background: none;
            padding: 0;
            border-radius: 0;
        }
        
        /* Code highlighting for different languages */
        .handout-content .codehilite {
            margin: 2rem 0;
            border-radius: 6px;
            overflow: hidden;
        }
        
        .handout-content .codehilite pre {
            margin: 0;
            border: none;
            border-radius: 0;
        }
        
        .last-updated {
            text-align: center;
            color: #606060;
            font-size: 0.9rem;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #d6d6d6;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            h1 {
                font-size: 2rem;
            }
            
            .course-grid {
                grid-template-columns: 1fr;
            }
            
            .course-meta .info-grid {
                grid-template-columns: 1fr;
            }
        }
        """
        
        css_path = self.output_dir / "styles.css"
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css_content)
        
        return "styles.css"
    
    def create_course_page(self, course_name, course_info, classes_data):
        """Create course index page with grouped materials and custom week titles"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Create enhanced course info section with new fields
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
            
            # Google Classroom Link
            if course_info.get('google_classroom_link'):
                info_items.append(f'<div class="info-item"><strong>Google Classroom:</strong> <a href="{course_info["google_classroom_link"]}" target="_blank">Access Classroom</a></div>')
            
            # Schedule Link
            if course_info.get('schedule_link'):
                if course_info.get('schedule_file'):
                    info_items.append(f'<div class="info-item"><strong>Schedule:</strong> <a href="schedule.html">View Schedule</a></div>')
                else:
                    info_items.append(f'<div class="info-item"><strong>Schedule:</strong> <a href="{course_info["schedule_link"]}" target="_blank">View Schedule</a></div>')
            
            # Textbook
            if course_info.get('textbook'):
                textbook = course_info['textbook']
                if textbook.lower().endswith('.pdf'):
                    textbook_path = self.classes_dir / course_name / textbook
                    if textbook_path.exists():
                        info_items.append(f'<div class="info-item"><strong>Textbook:</strong> <a href="{textbook}" target="_blank">Download PDF</a></div>')
                    else:
                        info_items.append(f'<div class="info-item"><strong>Textbook:</strong> {textbook}</div>')
                elif textbook.startswith('http'):
                    info_items.append(f'<div class="info-item"><strong>Textbook:</strong> <a href="{textbook}" target="_blank">View Online</a></div>')
                else:
                    info_items.append(f'<div class="info-item"><strong>Textbook:</strong> {textbook}</div>')
            
            # Description section
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
        
        # Create classes section with grouped materials and custom titles
        classes_html = ""
        for class_dir, materials in sorted(classes_data.items()):
            # Use custom week title if available, otherwise format folder name
            class_name = self.get_week_title(course_info, class_dir)
            
            # Group materials by type
            slides_html = ""
            handouts_html = ""
            pdfs_html = ""
            links_html = ""
            
            # Slides section
            if 'slides' in materials and materials['slides']:
                slides_html = '<div class="materials-section"><h4>Slides</h4><ul class="materials-list">'
                for slide_info in materials['slides']:
                    slides_html += f'<li><a href="{class_dir}/{slide_info["filename"]}">📊 {slide_info["title"]}</a></li>'
                slides_html += '</ul></div>'
            
            # Handouts section
            if 'handouts' in materials and materials['handouts']:
                handouts_html = '<div class="materials-section"><h4>Handouts</h4><ul class="materials-list">'
                for handout_info in materials['handouts']:
                    handouts_html += f'<li><a href="{class_dir}/{handout_info["filename"]}">📄 {handout_info["title"]}</a></li>'
                handouts_html += '</ul></div>'
            
            # PDFs section
            if 'pdfs' in materials and materials['pdfs']:
                pdfs_html = '<div class="materials-section"><h4>Documents</h4><ul class="materials-list">'
                for pdf_name in sorted(materials['pdfs']):
                    pdfs_html += f'<li><a href="{class_dir}/{pdf_name}" target="_blank">📎 {pdf_name}</a></li>'
                pdfs_html += '</ul></div>'
            
            # Links section
            if 'links' in materials and materials['links']:
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
    
    def create_main_index(self, courses_info, instructor_name="Dr. [Your Name]"):
        """Create main index page with instructor name and semester info"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        courses_html = ""
        for course_name, course_info in sorted(courses_info.items()):
            course_title = course_info.get('title', course_name.upper())
            description = course_info.get('description', 'Literature Course Materials')
            times = course_info.get('times', '')
            semester = course_info.get('semester', '')
            room = course_info.get('room', '')
            
            preview_info = []
            if semester:
                preview_info.append(f"📅 {semester}")
            if times:
                preview_info.append(f"⏰ {times}")
            if room:
                preview_info.append(f"📍 {room}")
            
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
    
    def generate_site(self):
        """Generate the complete static site with simple material sharing"""
        print(f"🚀 Generating literature course website...")
        print(f"📁 Processing materials from: {self.classes_dir}")
        print(f"📁 Output directory: {self.output_dir}")
        
        # Create output directory
        if self.output_dir.exists():
            # Only remove HTML and CSS files, keep compressed images and PDFs
            for item in self.output_dir.rglob("*.html"):
                item.unlink()
            for item in self.output_dir.rglob("*.css"):
                item.unlink()
        else:
            self.output_dir.mkdir()
        
        # Create CSS file
        css_file = self.create_css_file()
        print(f"✅ Created {css_file}")
        
        courses_info = {}
        total_classes = 0
        total_materials = 0
        
        # Global images directory
        global_images_dir = Path("images")
        
        # Process each course directory
        for course_dir in self.classes_dir.iterdir():
            if course_dir.is_dir():
                course_name = course_dir.name
                print(f"\n📚 Processing course: {course_name.upper()}")
                
                # Parse course information
                course_info = self.parse_course_info(course_dir)
                courses_info[course_name] = course_info
                
                # Create course output directory
                course_output_dir = self.output_dir / course_name
                course_output_dir.mkdir(exist_ok=True)
                
                # Generate schedule page if schedule file exists
                if course_info.get('schedule_file'):
                    try:
                        with open(course_info['schedule_file'], 'r', encoding='utf-8') as f:
                            schedule_content = f.read()
                        
                        schedule_html = self.create_schedule_page(schedule_content, course_name, course_info)
                        with open(course_output_dir / "schedule.html", 'w', encoding='utf-8') as f:
                            f.write(schedule_html)
                        print(f"    📅 Generated schedule page")
                    except Exception as e:
                        print(f"    ❌ Error generating schedule page: {e}")
                
                # Copy textbook PDF if it exists
                textbook_pdf = course_dir / course_info.get('textbook', '')
                if course_info.get('textbook') and course_info['textbook'].lower().endswith('.pdf') and textbook_pdf.exists():
                    try:
                        shutil.copy2(textbook_pdf, course_output_dir / textbook_pdf.name)
                        print(f"    📚 Copied textbook: {textbook_pdf.name}")
                    except Exception as e:
                        print(f"    ❌ Error copying textbook: {e}")
                
                # Compress and copy images for this course
                if global_images_dir.exists():
                    print(f"    🖼️  Processing images...")
                    self.compress_and_copy_images(global_images_dir, course_output_dir)
                
                # Determine materials source (this course or shared from another)
                materials_source_dir, source_course_name = self.get_materials_source(course_name, course_info)
                
                classes_data = {}
                
                # Process class directories from the materials source
                for class_dir in materials_source_dir.iterdir():
                    if class_dir.is_dir() and class_dir.name != "images":
                        class_name = class_dir.name
                        class_output_dir = course_output_dir / class_name
                        class_output_dir.mkdir(exist_ok=True)
                        
                        if source_course_name != course_name:
                            print(f"  📅 Processing shared class: {class_name} (from {source_course_name})")
                        else:
                            print(f"  📅 Processing class: {class_name}")
                        
                        # Copy class-specific images if they exist
                        self.copy_class_images(class_dir, class_output_dir)
                        
                        materials = {
                            'slides': [],
                            'handouts': [],
                            'pdfs': [],
                            'links': []
                        }
                        class_materials = 0
                        
                        # Get markdown files and categorize them
                        slide_files, handout_files = self.get_markdown_files(class_dir)
                        
                        # Process slide files
                        for slide_file in slide_files:
                            title = self.extract_title_from_markdown(slide_file)
                            output_filename = f"{slide_file.stem}.html"
                            output_path = class_output_dir / output_filename
                            
                            # Try marp-cli first, then fallback to browser-based
                            if self.marp_cli_available:
                                if self.convert_marp_with_cli(slide_file, output_path):
                                    # Enhance the generated HTML
                                    self.enhance_marp_html(output_path, title, course_name, class_name)
                                    print(f"    📊 Slides (CLI): {title}")
                                else:
                                    # Fallback to browser-based
                                    with open(slide_file, 'r', encoding='utf-8') as f:
                                        slides_content = f.read()
                                    
                                    slides_html = self.create_marp_viewer_fallback(
                                        slides_content, title, course_name, class_name
                                    )
                                    with open(output_path, 'w', encoding='utf-8') as f:
                                        f.write(slides_html)
                                    print(f"    📊 Slides (Browser): {title}")
                            else:
                                # Browser-based rendering
                                with open(slide_file, 'r', encoding='utf-8') as f:
                                    slides_content = f.read()
                                
                                slides_html = self.create_marp_viewer_fallback(
                                    slides_content, title, course_name, class_name
                                )
                                with open(output_path, 'w', encoding='utf-8') as f:
                                    f.write(slides_html)
                                print(f"    📊 Slides (Browser): {title}")
                            
                            materials['slides'].append({
                                'title': title,
                                'filename': output_filename
                            })
                            class_materials += 1
                        
                        # Process handout files
                        for handout_file in handout_files:
                            title = self.extract_title_from_markdown(handout_file)
                            output_filename = f"{handout_file.stem}.html"
                            
                            with open(handout_file, 'r', encoding='utf-8') as f:
                                handout_content = f.read()
                            
                            handout_html = self.create_handout_page(
                                handout_content, title, course_name, class_name
                            )
                            with open(class_output_dir / output_filename, 'w', encoding='utf-8') as f:
                                f.write(handout_html)
                            
                            materials['handouts'].append({
                                'title': title,
                                'filename': output_filename
                            })
                            print(f"    📄 Handout: {title}")
                            class_materials += 1
                        
                        # Process PDFs
                        pdf_files = self.get_all_pdfs(class_dir)
                        if pdf_files:
                            for pdf_file in pdf_files:
                                shutil.copy2(pdf_file, class_output_dir / pdf_file.name)
                                materials['pdfs'].append(pdf_file.name)
                                print(f"    📎 PDF: {pdf_file.name}")
                                class_materials += 1
                        
                        # Process links
                        links_file = class_dir / "links.txt"
                        if links_file.exists():
                            links = self.parse_links_file(links_file)
                            if links:
                                materials['links'] = links
                                for title, url in links:
                                    print(f"    🔗 Link: {title}")
                                    class_materials += 1
                        
                        classes_data[class_name] = materials
                        total_materials += class_materials
                        total_classes += 1
                
                # Create course index page (uses course-specific info but shared materials)
                course_html = self.create_course_page(course_name, course_info, classes_data)
                with open(course_output_dir / "index.html", 'w', encoding='utf-8') as f:
                    f.write(course_html)
                
                print(f"  ✅ Course page created")
        
        # Create main index page (you can customize instructor name here)
        main_html = self.create_main_index(courses_info, instructor_name="Pedro Groppo")
        with open(self.output_dir / "index.html", 'w', encoding='utf-8') as f:
            f.write(main_html)
        
        print(f"\n🎉 Website generated successfully!")
        print(f"📊 Summary:")
        print(f"   📚 Courses: {len(courses_info)}")
        print(f"   📅 Classes: {total_classes}")
        print(f"   📄 Materials: {total_materials}")
        print(f"\n🌐 Open {self.output_dir}/index.html in your browser")

def main():
    """Main function to run the generator"""
    generator = LiteratureCourseGenerator()
    
    if not generator.classes_dir.exists():
        print(f"❌ Classes directory '{generator.classes_dir}' not found.")
        print("Please create your course materials in the classes/ directory.")
        return
    
    generator.generate_site()

if __name__ == "__main__":
    main()
            