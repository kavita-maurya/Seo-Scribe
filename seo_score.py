from textstat import flesch_reading_ease
import re

def calculate_seo_score(blog_post):
    # Define weights for different factors
    WEIGHT_FLESCH = 0.3
    WEIGHT_KEYWORD_DENSITY = 0.2
    WEIGHT_HEADING_COUNT = 0.1
    WEIGHT_META_DESCRIPTION = 0.2
    WEIGHT_CONTENT_QUALITY = 0.2

    # Calculate Flesch Reading Ease score (higher is better)
    flesch_score = flesch_reading_ease(blog_post)

    # Calculate keyword density
    keywords = ['example', 'keywords', 'to', 'monitor']  # Replace with actual keywords
    words = re.findall(r'\w+', blog_post.lower())
    word_count = len(words)
    keyword_count = sum(1 for word in words if word in keywords)
    keyword_density = keyword_count / word_count

    # Calculate heading usage
    heading_count = len(re.findall(r'<h[1-6]', blog_post, re.IGNORECASE))

    # Calculate meta description length
    meta_description = "Sample meta description."  # Replace with actual meta description
    meta_description_length = len(meta_description)

    # Calculate content quality (a simple measure based on word count)
    content_quality = min(1, len(words) / 1000)  # Normalize to a value between 0 and 1

    # Calculate overall score
    seo_score = (
        (flesch_score / 100) * WEIGHT_FLESCH +
        keyword_density * WEIGHT_KEYWORD_DENSITY +
        (heading_count / 2) * WEIGHT_HEADING_COUNT +
        (1 - (meta_description_length / 160)) * WEIGHT_META_DESCRIPTION +
        content_quality * WEIGHT_CONTENT_QUALITY
    ) * 100

    return round(seo_score,2)
