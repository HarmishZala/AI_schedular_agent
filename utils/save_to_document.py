import os
import datetime

def save_document(response_text: str, directory: str = "./output"):
    """Export scheduling result or event summary to Markdown file with proper formatting"""
    os.makedirs(directory, exist_ok=True)

    # Create markdown content with metadata header
    markdown_content = f"""# 🗓️ AI Scheduler Result

    # **Generated:** {datetime.datetime.now().strftime('%Y-%m-%d at %H:%M')}  
    # **Created by:** AI Scheduler Agent

    ---

    {response_text}

    ---

    *This schedule was generated by AI. Please verify all information, especially times and event details before relying on your calendar.*
    """
            
    try:
        # Write to markdown file with UTF-8 encoding
        # Generate timestamp-based filename
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{directory}/AI_Scheduler_{timestamp}.md"

        print(filename)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Markdown file saved as: {filename}")
        return filename
        
    except Exception as e:
        print(f"Error saving markdown file: {e}")
        return None