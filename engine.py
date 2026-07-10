import random
import json
import os
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from PIL.ExifTags import TAGS
    EXIF_AVAILABLE = PIL_AVAILABLE
except ImportError:
    EXIF_AVAILABLE = False

PLATFORM_CONFIG = {
    "Adobe Stock": {
        "max_keywords": 50,
        "title_max_length": 100,
        "desc_max_length": 500,
        "categories": ["Animals", "Business", "Education", "Food", "Holidays",
                       "Industry", "Nature", "Objects", "People", "Technology",
                       "Travel", "Vector", "Background", "Abstract", "Sports"],
        "file_types": [".jpg", ".jpeg", ".png", ".tiff", ".eps", ".ai", ".svg"]
    },
    "Shutterstock": {
        "max_keywords": 50,
        "title_max_length": 200,
        "desc_max_length": 2000,
        "categories": ["Abstract", "Animals/Wildlife", "Arts", "Backgrounds",
                       "Beauty/Fashion", "Business", "Celebrities", "Editorial",
                       "Education", "Food/Drink", "Healthcare/Medical", "Holidays",
                       "Industrial", "Nature", "Objects", "Parks/Outdoor",
                       "People", "Religion", "Science", "Signs/Symbols",
                       "Sports/Recreation", "Technology", "Transportation", "Vintage"],
        "file_types": [".jpg", ".jpeg", ".png", ".eps", ".ai", ".svg", ".psd"]
    }
}

FILE_CATEGORIES = {
    ".jpg": "photo", ".jpeg": "photo", ".png": "photo",
    ".webp": "photo", ".bmp": "photo", ".tiff": "photo",
    ".svg": "vector", ".ai": "vector", ".eps": "vector",
    ".mp4": "video", ".mov": "video", ".avi": "video",
    ".psd": "design", ".tif": "photo"
}


class ImageAnalyzer:
    @staticmethod
    def analyze(filepath):
        ext = Path(filepath).suffix.lower()
        result = {
            "filepath": filepath,
            "filename": Path(filepath).stem,
            "extension": ext,
            "file_type": FILE_CATEGORIES.get(ext, "unknown"),
            "width": 0, "height": 0,
            "orientation": "unknown",
            "dominant_colors": [],
            "brightness": "unknown",
            "is_photo": ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"],
            "is_vector": ext in [".svg", ".ai", ".eps"],
            "is_video": ext in [".mp4", ".mov", ".avi"],
            "exif": {},
            "has_transparency": False,
            "file_size_kb": 0,
            "aspect_ratio": 0
        }

        try:
            result["file_size_kb"] = round(os.path.getsize(filepath) / 1024, 1)
        except:
            pass

        if result["is_photo"] and PIL_AVAILABLE:
            try:
                img = Image.open(filepath)
                result["width"], result["height"] = img.size
                result["aspect_ratio"] = round(result["width"] / result["height"], 2) if result["height"] > 0 else 0

                if result["width"] > result["height"] * 1.1:
                    result["orientation"] = "landscape"
                elif result["height"] > result["width"] * 1.1:
                    result["orientation"] = "portrait"
                else:
                    result["orientation"] = "square"

                result["has_transparency"] = img.mode in ("RGBA", "LA") or (
                    img.mode == "P" and "transparency" in img.info
                )

                if EXIF_AVAILABLE:
                    exif_data = img.getexif()
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if isinstance(value, (str, int, float)):
                            result["exif"][tag] = value

                result["dominant_colors"] = ImageAnalyzer._get_dominant_colors(img)
                result["brightness"] = ImageAnalyzer._get_brightness(img)
                img.close()
            except Exception:
                pass

        elif result["is_vector"] and PIL_AVAILABLE:
            try:
                img = Image.open(filepath)
                result["width"], result["height"] = img.size
                result["aspect_ratio"] = round(result["width"] / result["height"], 2) if result["height"] > 0 else 0

                if result["width"] > result["height"] * 1.1:
                    result["orientation"] = "landscape"
                elif result["height"] > result["width"] * 1.1:
                    result["orientation"] = "portrait"
                else:
                    result["orientation"] = "square"

                result["dominant_colors"] = ImageAnalyzer._get_dominant_colors(img)
                img.close()
            except Exception:
                pass

        else:
            result["orientation"] = "unknown"
            result["has_transparency"] = False

        return result

    @staticmethod
    def _get_dominant_colors(img, count=5):
        try:
            if img.mode != "RGB":
                img = img.convert("RGB")
            small = img.copy()
            small.thumbnail((100, 100))
            pixels = list(small.getdata())
            if not pixels:
                return []

            color_count = {}
            for pixel in pixels:
                r, g, b = pixel
                quantized = (r // 32 * 32, g // 32 * 32, b // 32 * 32)
                color_count[quantized] = color_count.get(quantized, 0) + 1

            sorted_colors = sorted(color_count.items(), key=lambda x: x[1], reverse=True)
            total = sum(c[1] for c in sorted_colors)

            named_colors = []
            for (r, g, b), cnt in sorted_colors[:count]:
                ratio = round(cnt / total * 100, 1)
                name = ImageAnalyzer._color_name(r, g, b)
                named_colors.append({"rgb": (r, g, b), "name": name, "ratio": ratio})
            return named_colors
        except Exception:
            return []

    @staticmethod
    def _color_name(r, g, b):
        colors_map = [
            ((255, 0, 0), "red"), ((200, 0, 0), "dark red"), ((255, 100, 100), "light red"),
            ((0, 255, 0), "green"), ((0, 200, 0), "dark green"), ((100, 255, 100), "light green"),
            ((0, 0, 255), "blue"), ((0, 0, 200), "dark blue"), ((100, 100, 255), "light blue"),
            ((255, 255, 0), "yellow"), ((255, 200, 0), "gold"), ((255, 255, 100), "light yellow"),
            ((255, 165, 0), "orange"), ((255, 140, 0), "dark orange"), ((255, 200, 100), "light orange"),
            ((255, 192, 203), "pink"), ((255, 105, 180), "hot pink"), ((200, 100, 200), "purple"),
            ((128, 0, 128), "purple"), ((75, 0, 130), "indigo"), ((138, 43, 226), "violet"),
            ((0, 0, 0), "black"), ((50, 50, 50), "dark gray"), ((128, 128, 128), "gray"),
            ((200, 200, 200), "light gray"), ((255, 255, 255), "white"),
            ((255, 255, 240), "ivory"), ((245, 245, 220), "beige"),
            ((165, 42, 42), "brown"), ((139, 69, 19), "saddle brown"),
            ((0, 255, 255), "cyan"), ((0, 128, 128), "teal"),
            ((127, 255, 212), "aquamarine"), ((64, 224, 208), "turquoise"),
            ((255, 20, 147), "deep pink"), ((219, 112, 147), "pale violet"),
            ((240, 230, 140), "khaki"), ((189, 183, 107), "dark khaki"),
            ((0, 100, 0), "dark green"), ((85, 107, 47), "olive"),
            ((160, 82, 45), "sienna"), ((210, 180, 140), "tan"),
            ((255, 228, 196), "bisque"), ((255, 235, 205), "blanched almond"),
            ((100, 149, 237), "cornflower blue"), ((70, 130, 180), "steel blue"),
            ((106, 90, 205), "slate blue"), ((123, 104, 238), "medium slate blue"),
            ((147, 112, 219), "medium purple"), ((218, 165, 32), "goldenrod"),
        ]

        best_name = "colorful"
        best_dist = 999999
        for (cr, cg, cb), name in colors_map:
            dist = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
            if dist < best_dist:
                best_dist = dist
                best_name = name

        if r > 200 and g > 200 and b > 200:
            return "white"
        if r < 50 and g < 50 and b < 50:
            return "black"
        if abs(r - g) < 30 and abs(g - b) < 30 and r > 100:
            return "gray"

        return best_name

    @staticmethod
    def _get_brightness(img):
        try:
            if img.mode != "RGB":
                img = img.convert("RGB")
            small = img.copy()
            small.thumbnail((50, 50))
            pixels = list(small.getdata())
            avg_brightness = sum((r * 0.299 + g * 0.587 + b * 0.114) for r, g, b in pixels) / len(pixels)
            if avg_brightness > 200:
                return "very bright"
            elif avg_brightness > 150:
                return "bright"
            elif avg_brightness > 100:
                return "medium"
            elif avg_brightness > 50:
                return "dark"
            else:
                return "very dark"
        except Exception:
            return "unknown"


class KeywordEngine:
    def __init__(self):
        self.db = self._build_database()
        self.analyzer = ImageAnalyzer()

    def _build_database(self):
        return {
            "nature": {
                "aliases": ["alam", "natural", "outdoor", "pemandangan", "landscape"],
                "synonyms": ["scenery", "wilderness", "environment", "countryside", "ecosystem",
                           "terrain", "habitat", "bioscape", "greenery", "flora"],
                "colors": ["green", "brown", "earth", "golden", "vibrant green",
                          "emerald", "forest green", "olive", "moss", "sage",
                          "terracotta", "umber", "sienna", "ochre", "taupe",
                          "sky blue", "azure", "cerulean", "teal", "turquoise"],
                "moods": ["serene", "calm", "peaceful", "tranquil", "fresh",
                         "natural", "organic", "pure", "clean", "pristine",
                         "breathtaking", "majestic", "awe-inspiring", "picturesque", "scenic"],
                "formats": ["landscape", "panoramic", "wide angle", "vertical", "horizontal",
                          "birds eye view", "aerial", "close up", "macro", "wide shot"],
                "seasons": ["spring", "summer", "autumn", "fall", "winter",
                          "rainy season", "dry season", "monsoon", "blooming season", "harvest"],
                "times": ["sunrise", "sunset", "golden hour", "blue hour", "dawn",
                         "dusk", "twilight", "morning", "afternoon", "night",
                         "midnight", "daytime", "evening", "sunlight", "moonlight"],
                "styles": ["realistic", "natural lighting", "soft focus", "vibrant",
                          "minimalist", "rustic", "authentic", "cinematic", "dramatic", "ethereal"],
                "subjects": {
                    "gunung": ["mountain", "peak", "summit", "volcano", "hill",
                              "highland", "alp", "ridge", "cliff", "slope",
                              "foggy mountain", "snow cap", "rock formation", "canyon", "valley"],
                    "pantai": ["beach", "coast", "shore", "seaside", "ocean",
                              "wave", "sand", "dune", "coral", "reef",
                              "tropical beach", "white sand", "turquoise water", "palm tree", "coastline"],
                    "hutan": ["forest", "jungle", "woods", "timberland", "rainforest",
                             "bamboo forest", "pine forest", "tropical forest", "dense forest", "canopy",
                             "treeline", "undergrowth", "shrubland", "bushland", "thicket"],
                    "sungai": ["river", "stream", "creek", "waterfall", "rapids",
                              "cascade", "brook", "tributary", "estuary", "delta",
                              "riverbank", "water flow", "freshwater", "riparian", "meander"],
                    "danau": ["lake", "pond", "lagoon", "reservoir", "glacial lake",
                             "crater lake", "oxbow lake", "salt lake", "reflection", "still water"],
                    "padang": ["field", "meadow", "grassland", "prairie", "savanna",
                              "plain", "pasture", "steppe", "pampas", "tundra"],
                    "bunga": ["flower", "blossom", "bloom", "petal", "pollen",
                             "wildflower", "garden", "floral", "botanical", "plant",
                             "tulip", "rose", "lotus", "orchid", "sunflower"],
                    "langit": ["sky", "cloud", "horizon", "atmosphere", "firmament",
                              "storm cloud", "rainbow", "lightning", "thunderstorm", "clear sky",
                              "starry night", "galaxy", "nebula", "aurora", "constellation"]
                }
            },
            "urban": {
                "aliases": ["kota", "city", "perkotaan", "urban area"],
                "synonyms": ["metropolitan", "municipal", "civic", "urbanized", "downtown",
                           "suburban", "inner city", "concrete jungle", "cityscape", "skyline"],
                "colors": ["gray", "steel", "concrete gray", "silver", "charcoal",
                          "slate", "neon", "fluorescent", "led", "bright",
                          "midnight blue", "navy", "indigo", "cobalt", "sapphire"],
                "moods": ["dynamic", "energetic", "vibrant", "bustling", "modern",
                         "sophisticated", "cosmopolitan", "trendy", "contemporary", "futuristic",
                         "crowded", "alive", "electric", "pulsing", "hustle"],
                "formats": ["architecture", "street view", "wide shot", "aerial", "night shot",
                          "long exposure", "timelapse", "perspective", "symmetry", "minimalist"],
                "times": ["blue hour", "golden hour", "night", "twilight", "rush hour",
                         "midnight", "early morning", "evening commute", "weekend", "holiday"],
                "styles": ["modern", "minimalist", "industrial", "futuristic", "vintage",
                          "grunge", "neon noir", "cyberpunk", "architectural", "street photography"],
                "subjects": {
                    "gedung": ["building", "skyscraper", "tower", "highrise", "office",
                              "apartment", "condominium", "plaza", "complex", "facade",
                              "glass building", "steel structure", "modern architecture", "landmark", "monument"],
                    "jalan": ["street", "road", "avenue", "boulevard", "highway",
                             "alley", "lane", "expressway", "flyover", "intersection",
                             "crosswalk", "sidewalk", "pedestrian", "pavement", "asphalt"],
                    "jembatan": ["bridge", "suspension bridge", "cable bridge", "arch bridge",
                                "footbridge", "viaduct", "overpass", "steel bridge", "concrete bridge", "span"],
                    "lampu": ["light", "street light", "neon", "lamp post", "illumination",
                             "chandelier", "spotlight", "floodlight", "lantern", "glow"],
                    "taman_kota": ["urban park", "public garden", "city square", "plaza",
                                  "green space", "recreation area", "playground", "fountain", "bench", "pathway"],
                    "transportasi": ["train", "subway", "bus", "taxi", "car",
                                    "motorcycle", "bicycle", "scooter", "tram", "transportation",
                                    "traffic", "vehicle", "commute", "travel", "transit"],
                    "jendela": ["window", "glass facade", "storefront", "display window",
                               "glass wall", "curtain wall", "window reflection", "shopping window", "pane", "framed view"]
                }
            },
            "teknologi": {
                "aliases": ["tech", "digital", "komputer", "IT", "technology"],
                "synonyms": ["innovation", "digital", "electronic", "automated", "smart",
                           "virtual", "cyber", "high tech", "cutting edge", "advanced",
                           "robotic", "automation", "AI", "machine learning", "blockchain"],
                "colors": ["blue", "cyan", "electric blue", "neon blue", "digital blue",
                          "silver", "white", "black", "dark gray", "metallic",
                          "led", "rgb", "holographic", "iridescent", "fluorescent"],
                "moods": ["innovative", "futuristic", "sleek", "minimal", "efficient",
                         "connected", "smart", "intelligent", "automated", "precise",
                         "modern", "advanced", "sophisticated", "digital", "virtual"],
                "formats": ["close up", "macro", "detail shot", "product shot", "studio shot",
                          "3d render", "digital art", "isometric", "flat lay", "minimalist"],
                "styles": ["modern", "minimalist", "clean", "sleek", "corporate",
                          "sci-fi", "cyberpunk", "holographic", "glitch", "tech wear"],
                "subjects": {
                    "komputer": ["computer", "laptop", "notebook", "workstation", "desktop",
                                "monitor", "screen", "display", "keyboard", "mouse",
                                "touchscreen", "ultrabook", "macbook", "chromebook", "gaming laptop"],
                    "smartphone": ["smartphone", "mobile", "phone", "cellphone", "handphone",
                                  "iphone", "android", "tablet", "ipad", "device",
                                  "touch screen", "app", "smart device", "mobile device", "gadget"],
                    "server": ["server", "data center", "cloud", "network", "database",
                              "storage", "rack", "mainframe", "hosting", "infrastructure",
                              "cybersecurity", "encryption", "firewall", "protocol", "bandwidth"],
                    "ai": ["artificial intelligence", "AI", "machine learning", "deep learning",
                          "neural network", "algorithm", "data science", "automation",
                          "robot", "chatbot", "smart system", "predictive", "analytics", "intelligent system"],
                    "coding": ["programming", "coding", "developer", "software", "code",
                              "script", "programmer", "hacker", "cybersecurity", "debug",
                              "python", "javascript", "html", "css", "algorithm"],
                    "robot": ["robot", "robotic", "automation", "droid", "humanoid",
                             "cyborg", "drone", "autonomous", "mechanical", "android",
                             "industrial robot", "robot arm", "ai robot", "future robot", "machine"],
                    "circuit": ["circuit board", "motherboard", "processor", "microchip", "semiconductor",
                               "cpu", "gpu", "electronics", "hardware", "component",
                               "transistor", "solder", "pcb", "integrated circuit", "nano technology"]
                }
            },
            "bisnis": {
                "aliases": ["business", "korporasi", "corporate", "professional", "kerja"],
                "synonyms": ["corporate", "enterprise", "commercial", "entrepreneurial", "professional",
                           "managerial", "organizational", "institutional", "financial", "marketing"],
                "colors": ["navy blue", "dark blue", "charcoal", "black", "white",
                          "gold", "silver", "burgundy", "forest green", "maroon",
                          "cream", "ivory", "beige", "taupe", "steel gray"],
                "moods": ["professional", "confident", "ambitious", "strategic", "focused",
                         "collaborative", "innovative", "growth", "successful", "efficient",
                         "determined", "driven", "corporate", "formal", "executive"],
                "formats": ["corporate headshot", "office setting", "meeting room", "conference", "presentation",
                          "team photo", "workspace", "coworking", "boardroom", "seminar"],
                "styles": ["corporate", "professional", "clean", "minimalist", "modern",
                          "business casual", "formal", "executive", "contemporary", "sleek"],
                "subjects": {
                    "meeting": ["meeting", "conference", "discussion", "brainstorm", "presentation",
                               "negotiation", "seminar", "workshop", "webinar", "board meeting",
                               "team meeting", "video conference", "zoom", "collaboration", "strategy session"],
                    "team": ["team", "employees", "colleagues", "coworkers", "staff",
                            "workforce", "department", "division", "group", "crew",
                            "teamwork", "collaboration", "partnership", "network", "team building"],
                    "office": ["office", "workspace", "coworking", "cubicle", "workstation",
                              "open office", "meeting room", "lobby", "reception", "break room",
                              "modern office", "creative office", "startup office", "executive office", "home office"],
                    "presentation": ["presentation", "slide", "chart", "graph", "data",
                                    "infographic", "report", "proposal", "pitch", "analysis",
                                    "powerpoint", "whiteboard", "projector", "screen", "dashboard"],
                    "success": ["success", "achievement", "growth", "profit", "revenue",
                              "goal", "target", "milestone", "award", "recognition",
                              "celebration", "victory", "accomplishment", "progress", "result"],
                    "startup": ["startup", "entrepreneur", "founder", "innovation", "venture",
                               "small business", "new company", "launch", "growth", "disruption",
                               "angel investor", "seed funding", "accelerator", "incubator", "pivot"],
                    "finance": ["finance", "banking", "investment", "stock market", "trading",
                               "currency", "money", "wealth", "accounting", "audit",
                               "financial planning", "portfolio", "asset", "capital", "fund"]
                }
            },
            "kesehatan": {
                "aliases": ["health", "medical", "sehat", "wellness", "klinik"],
                "synonyms": ["wellness", "fitness", "nutrition", "medical", "therapeutic",
                           "holistic", "preventive", "curative", "diagnostic", "clinical",
                           "healthcare", "remedial", "recuperative", "restorative", "rehabilitative"],
                "colors": ["white", "blue", "light blue", "green", "teal",
                          "sterile white", "medical green", "cyan", "ice blue", "mint",
                          "pastel", "soft", "clean white", "hospital blue", "sage"],
                "moods": ["healthy", "fresh", "clean", "pure", "vibrant",
                         "energetic", "balanced", "peaceful", "calm", "healing",
                         "rejuvenating", "refreshing", "invigorating", "nurturing", "soothing"],
                "formats": ["close up", "studio shot", "clinical", "clean shot", "wellness shot",
                          "medical document", "infographic", "before after", "step by step", "instructional"],
                "styles": ["clean", "sterile", "professional", "clinical", "minimalist",
                          "modern", "scientific", "educational", "documentary", "healthcare"],
                "subjects": {
                    "dokter": ["doctor", "physician", "surgeon", "specialist", "nurse",
                              "medical professional", "healthcare worker", "dentist", "therapist", "practitioner",
                              "general practitioner", "pediatrician", "cardiologist", "dermatologist", "neurologist"],
                    "rumah_sakit": ["hospital", "clinic", "medical center", "healthcare facility",
                                   "emergency room", "operating room", "ward", "pharmacy", "laboratory", "recovery room"],
                    "obat": ["medicine", "pill", "capsule", "tablet", "vaccine",
                            "prescription", "drug", "remedy", "medication", "treatment",
                            "antibiotic", "vitamin", "supplement", "injection", "therapy"],
                    "fitness": ["fitness", "exercise", "workout", "gym", "training",
                               "yoga", "meditation", "pilates", "cardio", "strength",
                               "running", "jogging", "cycling", "swimming", "stretching"],
                    "makanan_sehat": ["healthy food", "nutrition", "balanced diet", "superfood", "organic",
                                     "vegetable", "fruit", "salad", "smoothie", "whole food",
                                     "plant based", "vegan", "vegetarian", "gluten free", "keto"],
                    "mental": ["mental health", "mindfulness", "meditation", "wellbeing", "self care",
                              "therapy", "counseling", "mental wellness", "stress relief", "relaxation",
                              "peace of mind", "balance", "harmony", "inner peace", "calmness"]
                }
            },
            "pendidikan": {
                "aliases": ["education", "sekolah", "learning", "study", "belajar"],
                "synonyms": ["academic", "educational", "scholastic", "intellectual", "pedagogical",
                           "instructional", "tutorial", "curricular", "didactic", "educational"],
                "colors": ["blue", "yellow", "red", "green", "warm",
                          "bright", "cheerful", "vibrant", "pastel", "primary colors"],
                "moods": ["inspiring", "motivating", "curious", "creative", "focused",
                         "eager", "determined", "enthusiastic", "bright", "optimistic",
                         "academic", "scholarly", "intellectual", "thoughtful", "reflective"],
                "formats": ["classroom", "library", "study room", "lecture hall", "laboratory",
                          "workshop", "tutorial", "educational chart", "diagram", "infographic"],
                "styles": ["educational", "academic", "formal", "colorful", "engaging",
                          "minimalist", "modern", "traditional", "creative", "interactive"],
                "subjects": {
                    "sekolah": ["school", "classroom", "campus", "academy", "institution",
                               "elementary school", "high school", "university", "college", "graduate school"],
                    "buku": ["book", "textbook", "library", "reading", "literature",
                            "knowledge", "study material", "reference", "encyclopedia", "journal",
                            "e-book", "digital book", "academic book", "manual", "guide"],
                    "matematika": ["mathematics", "math", "algebra", "geometry", "calculus",
                                  "statistics", "equation", "formula", "number", "calculation",
                                  "arithmetic", "trigonometry", "logic", "problem solving", "graph"],
                    "sains": ["science", "biology", "chemistry", "physics", "laboratory",
                             "experiment", "research", "scientific", "discovery", "innovation",
                             "microscope", "test tube", "beaker", "molecule", "dna"],
                    "online_learning": ["online learning", "e-learning", "distance learning", "virtual classroom",
                                       "webinar", "online course", "mooc", "digital learning", "remote education",
                                       "zoom class", "video tutorial", "self study", "online education", "cyber school"],
                    "anak_murid": ["student", "pupil", "learner", "graduate", "scholar",
                                  "undergraduate", "postgraduate", "classmate", "peer", "apprentice"]
                }
            },
            "makanan": {
                "aliases": ["food", "kuliner", "masakan", "cuisine", "restaurant"],
                "synonyms": ["culinary", "gastronomic", "epicurean", "gourmet", "delectable",
                           "delicious", "savory", "flavorful", "exquisite", "tasty",
                           "appetizing", "mouthwatering", "succulent", "luscious", "palatable"],
                "colors": ["red", "orange", "yellow", "golden", "green",
                          "brown", "cream", "maroon", "burgundy", "crimson",
                          "vibrant", "rich", "warm", "appetizing", "natural"],
                "moods": ["delicious", "tempting", "appetizing", "fresh", "warm",
                         "comforting", "indulgent", "satisfying", "delectable", "hearty",
                         "exquisite", "gourmet", "artisanal", "homemade", "authentic"],
                "formats": ["close up", "macro", "birds eye view", "flat lay", "overhead",
                          "table setting", "plating", "food styling", "recipe shot", "menu design"],
                "styles": ["gourmet", "food photography", "artisanal", "rustic", "modern",
                          "traditional", "street food", "fine dining", "casual", "homestyle"],
                "subjects": {
                    "masakan_indo": ["Indonesian food", "nasi", "sate", "rendang", "sambal",
                                    "gado gado", "bakso", "mie ayam", "nasi goreng", "ayam",
                                    "traditional food", "spicy food", "herbs and spices", "kecap", "emping"],
                    "masakan_asia": ["Asian food", "sushi", "ramen", "dim sum", "pho",
                                    "curry", "stir fry", "noodles", "rice bowl", "tempura",
                                    "teriyaki", "wasabi", "ginger", "soy sauce", "sesame"],
                    "makanan_barat": ["western food", "pasta", "pizza", "burger", "steak",
                                     "sandwich", "salad", "soup", "bread", "cheese",
                                     "grilled", "roasted", "baked", "fried", "toasted"],
                    "kue": ["dessert", "cake", "pastry", "chocolate", "ice cream",
                           "cookie", "brownie", "pie", "pudding", "macaron",
                           "cupcake", "donut", "croissant", "candy", "sweet"],
                    "minuman": ["drink", "beverage", "coffee", "tea", "juice",
                               "smoothie", "cocktail", "mocktail", "wine", "beer",
                               "espresso", "latte", "cappuccino", "matcha", "soda"],
                    "sayur_buah": ["vegetable", "fruit", "produce", "fresh", "organic",
                                  "tomato", "broccoli", "carrot", "spinach", "avocado",
                                  "berry", "citrus", "apple", "banana", "grape"]
                }
            },
            "olahraga": {
                "aliases": ["sport", "fitness", "exercise", "game", "permainan"],
                "synonyms": ["athletic", "sporting", "competitive", "physical", "recreational",
                           "active", "energetic", "dynamic", "vigorous", "strenuous"],
                "colors": ["red", "blue", "green", "yellow", "white",
                          "black", "neon", "fluorescent", "bright", "vibrant",
                          "team colors", "sport blue", "athletic red", "field green", "court orange"],
                "moods": ["energetic", "dynamic", "powerful", "active", "competitive",
                         "motivated", "determined", "focused", "passionate", "triumphant",
                         "victorious", "intense", "athletic", "agile", "swift"],
                "formats": ["action shot", "motion blur", "dynamic angle", "wide shot", "close up",
                          "slow motion", "high speed", "low angle", "sports photography", "game action"],
                "styles": ["sports", "action", "dynamic", "energetic", "professional",
                          "competitive", "athletic", "modern", "sporty", "urban sport"],
                "subjects": {
                    "sepak_bola": ["soccer", "football", "stadium", "match", "player",
                                  "ball", "goal", "kick", "score", "champion",
                                  "world cup", "league", "tournament", "team", "competition"],
                    "basket": ["basketball", "hoop", "court", "dribble", "slam dunk",
                              "nba", "playground", "basketball player", "jumpshot", "rebound"],
                    "lari": ["running", "sprint", "marathon", "race", "track",
                            "jogging", "athlete", "runner", "speed", "endurance",
                            "fitness run", "trail running", "road race", "relay", "finish line"],
                    "renang": ["swimming", "pool", "lap", "swimmer", "dive",
                              "butterfly stroke", "freestyle", "backstroke", "breaststroke", "aquatic"],
                    "sepeda": ["cycling", "bicycle", "bike", "road bike", "mountain bike",
                              "cyclist", "tour de france", "pedal", "helmet", "trail"],
                    "yoga": ["yoga", "meditation", "pilates", "stretching", "flexibility",
                            "wellness", "balance", "pose", "asana", "mindfulness",
                            "yoga mat", "meditation pose", "lotus", "downward dog", "warrior pose"]
                }
            },
            "seni": {
                "aliases": ["art", "artistic", "kreatif", "creative", "design"],
                "synonyms": ["creative", "artistic", "aesthetic", "visual", "expressive",
                           "imaginative", "original", "innovative", "inspired", "avant garde",
                           "contemporary", "abstract", "conceptual", "experimental", "evocative"],
                "colors": ["all colors", "vibrant", "pastel", "monochrome", "bold",
                          "bright", "muted", "earth tones", "rainbow", "spectrum",
                          "primary", "secondary", "complementary", "analogous", "warm palette"],
                "moods": ["creative", "inspiring", "expressive", "emotional", "thought provoking",
                         "imaginative", "dreamy", "surreal", "whimsical", "dramatic",
                         "abstract", "bold", "contemplative", "passionate", "free"],
                "formats": ["fine art", "digital art", "mixed media", "canvas", "sculpture",
                          "installation", "gallery", "exhibition", "studio", "performance"],
                "styles": ["abstract", "modern", "contemporary", "classic", "surreal",
                          "pop art", "minimalist", "expressionist", "impressionist", "cubist",
                          "art deco", "art nouveau", "baroque", "renaissance", "street art"],
                "subjects": {
                    "lukisan": ["painting", "oil painting", "watercolor", "acrylic", "canvas",
                               "brushstroke", "palette", "easel", "paint", "masterpiece",
                               "abstract painting", "landscape painting", "portrait", "still life", "artwork"],
                    "fotografi": ["photography", "camera", "lens", "photographer", "shot",
                                 "composition", "exposure", "aperture", "shutter", "focus",
                                 "portrait photography", "landscape photography", "street photography",
                                 "macro photography", "fine art photography"],
                    "ilustrasi": ["illustration", "drawing", "sketch", "digital illustration",
                                 "vector", "graphic", "doodle", "line art", "ink", "charcoal",
                                 "children illustration", "editorial illustration", "fashion illustration",
                                 "technical drawing", "concept art"],
                    "desain_grafis": ["graphic design", "typography", "layout", "poster", "logo",
                                     "branding", "identity", "creative design", "visual communication",
                                     "social media design", "web design", "ui design", "print design",
                                     "packaging", "motion graphics"],
                    "patung": ["sculpture", "statue", "carving", "bronze", "marble",
                              "installation", "3d art", "figurine", "bust", "abstract sculpture"],
                    "musik": ["music", "musician", "instrument", "concert", "performance",
                             "guitar", "piano", "drums", "violin", "singer",
                             "orchestra", "band", "stage", "recording", "studio"]
                }
            },
            "abstrak": {
                "aliases": ["abstract", "pattern", "tekstur", "geometry"],
                "synonyms": ["abstract", "non representational", "conceptual", "geometric", "organic",
                           "fractal", "textural", "patterned", "decorative", "ornamental",
                           "minimal", "modernist", "formless", "amorphous", "ethereal"],
                "colors": ["gradient", "vibrant", "neon", "pastel", "monochrome",
                          "duotone", "iridescent", "holographic", "metallic", "fluorescent",
                          "earth tones", "ocean blue", "sunset", "aurora", "rainbow"],
                "moods": ["abstract", "modern", "sophisticated", "mysterious", "contemplative",
                         "dynamic", "flowing", "organic", "geometric", "minimal",
                         "ethereal", "surreal", "dreamy", "cosmic", "futuristic"],
                "formats": ["pattern", "texture", "background", "wallpaper", "seamless",
                          "geometric", "abstract", "fractal", "gradient", "overlay"],
                "styles": ["abstract", "geometric", "organic", "minimalist", "modern",
                          "pop art", "line art", "watercolor effect", "digital art", "3d render"],
                "subjects": {
                    "geometris": ["geometric", "shape", "pattern", "symmetry", "mandala",
                                 "hexagon", "triangle", "circle", "square", "diamond",
                                 "geometric pattern", "abstract geometry", "sacred geometry", "tessellation", "polygon"],
                    "tekstur": ["texture", "surface", "grain", "rough", "smooth",
                               "wood texture", "marble texture", "concrete texture", "paper texture",
                               "fabric texture", "metal texture", "stone texture", "brick texture", "sand texture"],
                    "gradasi": ["gradient", "fade", "blend", "ombre", "transition",
                               "color gradient", "mesh gradient", "linear gradient", "radial gradient",
                               "sunset gradient", "neon gradient", "pastel gradient", "dark gradient"],
                    "liquid": ["liquid", "fluid", "paint", "ink", "splash",
                              "water", "oil", "marble", "swirl", "vortex",
                              "liquid art", "fluid art", "acrylic pour", "ink drop", "bubble"],
                    "garis": ["line", "curve", "wave", "spiral", "stripe",
                             "line art", "minimal line", "continuous line", "abstract line",
                             "dotted", "dashed", "zigzag", "parallel", "intersecting"],
                    "latar_belakang": ["background", "wallpaper", "backdrop", "surface", "canvas",
                                       "abstract background", "gradient background", "pattern background",
                                       "texture background", "solid background", "dark background", "light background"]
                }
            },
            "travel": {
                "aliases": ["travel", "trip", "liburan", "holiday", "vacation"],
                "synonyms": ["tourism", "traveling", "journey", "expedition", "adventure",
                           "exploration", "excursion", "voyage", "touring", "discovery",
                           "wanderlust", "nomadic", "globetrotting", "backpacking", "sightseeing"],
                "colors": ["warm", "golden", "sunny", "tropical", "ocean blue",
                          "sand", "coral", "palm green", "sky blue", "vibrant",
                          "earthy", "terracotta", "turquoise", "saffron", "azure"],
                "moods": ["adventurous", "excited", "free", "wanderlust", "exploring",
                         "discovery", "thrilled", "joyful", "carefree", "curious",
                         "inspired", "amazed", "wonder", "exotic", "authentic"],
                "formats": ["travel photography", "landscape", "street scene", "aerial", "documentary",
                          "vacation snap", "travelogue", "destination shot", "cultural", "architectural"],
                "styles": ["travel", "documentary", "lifestyle", "authentic", "vibrant",
                          "warm tone", "golden hour", "candid", "storytelling", "adventure"],
                "subjects": {
                    "destinasi": ["destination", "landmark", "attraction", "wonder", "resort",
                                 "beach destination", "mountain destination", "city break", "cultural site",
                                 "heritage site", "unesco", "tropical paradise", "exotic place"],
                    "budaya": ["culture", "tradition", "heritage", "custom", "ceremony",
                              "festival", "celebration", "ritual", "indigenous", "ethnic",
                              "cultural dance", "traditional costume", "local culture", "folk", "artisan"],
                    "petualangan": ["adventure", "trekking", "hiking", "camping", "exploring",
                                   "backpacking", "road trip", "safari", "diving", "climbing",
                                   "wilderness", "off road", "survival", "expedition", "extreme travel"],
                    "transportasi": ["airplane", "flight", "airport", "train", "boat",
                                    "cruise", "ferry", "car rental", "motorcycle", "bicycle",
                                    "travel by air", "travel by land", "travel by sea", "public transport", "taxi"],
                    "akomodasi": ["hotel", "resort", "villa", "hostel", "inn",
                                 "accommodation", "lobby", "pool", "spa", "suite",
                                 "luxury hotel", "boutique hotel", "budget hotel", "beach resort", "mountain lodge"],
                    "kuliner_travel": ["local food", "street food", "food market", "culinary tour",
                                       "traditional cuisine", "food travel", "foodie", "local delicacy",
                                       "night market", "food stall", "cooking class", "taste of local"]
                }
            }
        }

    def _flatten_subjects(self, category_data):
        keywords = []
        for subcat, items in category_data.get("subjects", {}).items():
            keywords.extend(items)
        return keywords

    def generate_keywords(self, base_word, max_keywords=50):
        base_word = base_word.lower().strip()
        keywords = [base_word]
        used = set()
        used.add(base_word)

        matched_categories = []
        for cat_name, cat_data in self.db.items():
            if base_word in cat_data.get("aliases", []):
                matched_categories.append((cat_name, cat_data, 1.0))
                continue
            if base_word in cat_data.get("synonyms", []):
                matched_categories.append((cat_name, cat_data, 0.9))
                continue
            for subcat, items in cat_data.get("subjects", {}).items():
                if base_word in items or base_word.lower() in [i.lower() for i in items]:
                    matched_categories.append((cat_name, cat_data, 0.8))
                    break
                for item in items:
                    if base_word in item.lower() or item.lower() in base_word:
                        matched_categories.append((cat_name, cat_data, 0.7))
                        break

            extra_fields = ["times", "seasons", "colors", "moods", "formats", "styles"]
            for field in extra_fields:
                if field in cat_data:
                    for val in cat_data[field]:
                        if base_word == val.lower() or val.lower() == base_word:
                            matched_categories.append((cat_name, cat_data, 0.85))
                            break
                    if matched_categories and matched_categories[-1][0] == cat_name:
                        break

        if not matched_categories:
            matched_categories = []
            best_score = 0
            for cat_name, cat_data in self.db.items():
                all_words = (cat_data.get("aliases", []) + cat_data.get("synonyms", []) +
                           self._flatten_subjects(cat_data))
                for w in all_words:
                    if base_word in w or w in base_word:
                        score = len(set(base_word) & set(w)) / max(len(base_word), len(w))
                        if score > best_score:
                            best_score = score
                            matched_categories = [(cat_name, cat_data, score)]

        for cat_name, cat_data, _ in matched_categories:
            for item in cat_data.get("synonyms", []):
                if item not in used:
                    keywords.append(item)
                    used.add(item)

            for mood in cat_data.get("moods", []):
                if mood not in used:
                    keywords.append(mood)
                    used.add(mood)

            for season in cat_data.get("seasons", []):
                if season not in used:
                    keywords.append(season)
                    used.add(season)

            for time_word in cat_data.get("times", []):
                if time_word not in used:
                    keywords.append(time_word)
                    used.add(time_word)

            for fmt in cat_data.get("formats", []):
                if fmt not in used:
                    keywords.append(fmt)
                    used.add(fmt)

            for style in cat_data.get("styles", []):
                if style not in used:
                    keywords.append(style)
                    used.add(style)

            for color in cat_data.get("colors", []):
                if color not in used:
                    keywords.append(color)
                    used.add(color)

            for subcat, items in cat_data.get("subjects", {}).items():
                for item in items:
                    if item not in used:
                        keywords.append(item)
                        used.add(item)

        if base_word not in [k.lower() for k in keywords[:10]]:
            keywords.insert(0, base_word)

        if len(keywords) < 20:
            more_terms = self._generate_related_terms(base_word)
            for term in more_terms:
                if term not in used:
                    keywords.append(term)
                    used.add(term)

        stock_suffixes = ["stock photo", "stock image", "stock photography", "royalty free",
                         "stock illustration", "stock vector", "high resolution", "hd wallpaper",
                         "photo", "image", "picture", "photograph", "visual", "graphic"]

        for suffix in stock_suffixes:
            if suffix not in used:
                keywords.append(suffix)
                used.add(suffix)

        return keywords[:max_keywords]

    def _generate_related_terms(self, word):
        return [
            f"{word} photography", f"{word} background", f"{word} wallpaper",
            f"{word} design", f"{word} concept", f"{word} art",
            f"beautiful {word}", f"amazing {word}", f"creative {word}",
            f"modern {word}", f"abstract {word}", f"digital {word}",
            f"professional {word}", f"unique {word}", f"artistic {word}",
            f"colorful {word}", f"elegant {word}", f"minimalist {word}",
            f"inspiring {word}", f"stunning {word}"
        ]

    def generate_titles(self, base_word, count=5):
        base = base_word.lower()
        templates = [
            f"Beautiful {base} scenery with soft natural light",
            f"Serene {base} landscape with calm atmosphere",
            f"Scenic view of {base} in golden hour lighting",
            f"Peaceful {base} scene with gentle breeze",
            f"Stunning {base} landscape in vivid colors",
            f"Quiet {base} morning with soft clouds",
            f"Wide panoramic view of {base} landscape",
            f"Natural {base} scenery with fresh green tones",
        ]
        selected = random.sample(templates, min(count, len(templates)))
        return selected

    def generate_descriptions(self, base_word, keywords, count=3):
        base = base_word.title()
        kw_sample = ", ".join(keywords[:10])
        kw_str = ", ".join(keywords[:15])

        desc_templates = [
            f"Discover this stunning collection of {base} stock photography. "
            f"Perfect for creative projects, marketing materials, and commercial use. "
            f"Includes high-quality images featuring {kw_sample}. "
            f"Ideal for designers, content creators, and businesses seeking professional visual content. "
            f"Royalty-free license included for commercial and editorial use.",

            f"Explore our premium {base} image collection. "
            f"This versatile stock photo features {kw_sample} "
            f"making it perfect for websites, social media, presentations, and print materials. "
            f"High-resolution format ensures crystal clear quality for any application. "
            f"Download instantly and use immediately in your creative projects.",

            f"Professional {base} stock photography for your creative needs. "
            f"This image captures the essence of {kw_str}. "
            f"Perfect for advertising, branding, web design, and editorial content. "
            f"Enhanced and optimized for immediate use. "
            f"Compatible with all major design software and platforms.",

            f"Beautiful {base} photograph showcasing {kw_sample}. "
            f"This royalty-free image is perfect for both personal and commercial projects. "
            f"Features stunning composition, vibrant colors, and professional lighting. "
            f"Available for instant download in high resolution. "
            f"Ideal for websites, blogs, social media, print, and marketing materials.",

            f"Captivating {base} stock image featuring {kw_str}. "
            f"This versatile visual asset is perfect for creative professionals, "
            f"marketers, and business owners. Use it for website headers, blog posts, "
            f"social media content, presentations, brochures, and more. "
            f"Includes standard royalty-free license."
        ]
        selected = random.sample(desc_templates, min(count, len(desc_templates)))
        return selected

    def generate_csv_data(self, base_word, num_keywords=50, num_titles=3, num_desc=1):
        keywords = self.generate_keywords(base_word, max_keywords=num_keywords)
        titles = self.generate_titles(base_word, count=num_titles)
        kw_str = ", ".join(keywords)

        rows = []
        for i in range(len(titles)):
            rows.append(self.get_platform_csv_row({
                "filename": f"{base_word.lower().replace(' ', '_')}_{i+1}.jpg",
                "title": titles[i],
                "keywords": kw_str,
                "category": self._guess_category(base_word)
            }))
        return rows

    def analyze_file(self, filepath):
        return self.analyzer.analyze(filepath)

    def generate_from_file(self, filepath, platform="Adobe Stock", num_keywords=50, num_titles=3, num_desc=1):
        analysis = self.analyzer.analyze(filepath)
        base_concept = self._extract_concept_from_analysis(analysis)
        platform_config = PLATFORM_CONFIG.get(platform, PLATFORM_CONFIG["Adobe Stock"])
        max_kw = min(num_keywords, platform_config["max_keywords"])

        keywords = self._generate_file_keywords(base_concept, analysis, max_kw)
        titles = self._generate_file_titles(base_concept, analysis, platform, num_titles)
        kw_str = ", ".join(keywords)

        rows = []
        for i in range(len(titles)):
            rows.append(self.get_platform_csv_row({
                "filename": f"{analysis['filename']}_{i+1}{analysis['extension']}",
                "title": titles[i][:platform_config.get("title_max_length", 200)],
                "keywords": kw_str,
                "category": self._guess_category(base_concept)
            }))
        return rows, analysis

    def _extract_concept_from_analysis(self, analysis):
        fname = analysis["filename"].lower().replace("_", " ").replace("-", " ").replace(".", " ")
        fname = " ".join(fname.split())

        stop_words = {"img", "image", "photo", "picture", "dsc", "dscn", "img_",
                     "photo_", "pic", "untitled", "screenshot", "export", "render",
                     "new", "copy", "final", "edit", "edited", "backup"}
        words = fname.split()
        meaningful = [w for w in words if w.lower() not in stop_words and len(w) > 2]

        if meaningful:
            return " ".join(meaningful[:3])

        colors = [c["name"] for c in analysis["dominant_colors"][:2]]
        if colors:
            base = f"{' and '.join(colors)}"
            if analysis["orientation"] != "unknown":
                base += f" {analysis['orientation']}"
            if analysis["file_type"] != "unknown":
                base += f" {analysis['file_type']}"
            textural_qualities = []
            if analysis["has_transparency"]:
                textural_qualities.append("transparent")
            if analysis["brightness"] in ["dark", "very dark"]:
                textural_qualities.append("dark")
            elif analysis["brightness"] in ["bright", "very bright"]:
                textural_qualities.append("bright")
            if textural_qualities:
                base = f"{' '.join(textural_qualities)} {base}"
            return base

        return analysis["file_type"].title()

    def _generate_file_keywords(self, base_concept, analysis, max_keywords=50):
        keywords = []
        used = set()

        def push(word):
            w = word.lower().strip()
            if w and w not in used:
                keywords.append(w)
                used.add(w)

        push(base_concept)

        for w in base_concept.split():
            push(w)

        push(analysis["filename"].lower())

        if analysis["file_type"] == "vector":
            push("vector"), push("vector graphic"), push("vector illustration")
            push("scalable vector"), push("svg"), push("vector art")
        elif analysis["file_type"] == "photo":
            push("photo"), push("photograph"), push("photography")
            push("stock photo"), push("high resolution")
        elif analysis["file_type"] == "video":
            push("video"), push("footage"), push("motion graphic")
            push("stock video"), push("hd video")
        elif analysis["file_type"] == "design":
            push("design"), push("graphic design"), push("creative design")

        if analysis["orientation"] == "landscape":
            push("landscape"), push("horizontal"), push("wide")
        elif analysis["orientation"] == "portrait":
            push("portrait"), push("vertical")
        elif analysis["orientation"] == "square":
            push("square"), push("square format")

        analysis_kw = self._keywords_from_analysis(analysis)
        for kw in analysis_kw:
            push(kw)

        for c in analysis["dominant_colors"][:3]:
            push(c["name"])
            push(f"{c['name']} color")

        if analysis["brightness"] != "unknown":
            push(analysis["brightness"])

        if analysis["has_transparency"]:
            push("transparent background"), push("transparency")
            push("isolated"), push("cut out")

        if analysis["width"] and analysis["height"]:
            push(f"{analysis['width']}x{analysis['height']}")
            if analysis["width"] >= 3840:
                push("4k"), push("ultra hd"), push("high resolution")
            elif analysis["width"] >= 1920:
                push("full hd"), push("hd"), push("high quality")

        matched_kw = self.generate_keywords(base_concept, max_keywords=100)
        for kw in matched_kw:
            push(kw)

        push("royalty free"), push("stock image"), push("stock photography")
        push("download"), push("commercial use"), push("creative project")

        return keywords[:max_keywords]

    def _keywords_from_analysis(self, analysis):
        result = []
        if analysis["brightness"] == "very bright" or analysis["brightness"] == "bright":
            result.extend(["bright", "well lit", "sunny", "clear", "vibrant"])
        elif analysis["brightness"] == "dark" or analysis["brightness"] == "very dark":
            result.extend(["dark", "moody", "atmospheric", "dramatic", "shadow"])

        colors = [c["name"] for c in analysis["dominant_colors"][:2]]
        if "black" in colors or "dark gray" in colors:
            result.append("monochrome")
        if "white" in colors and "black" in colors:
            result.append("high contrast")

        return result

    def _generate_file_titles(self, base_concept, analysis, platform, count=3):
        base = base_concept.lower().strip() if base_concept else "abstract"
        col_names = [c["name"] for c in analysis["dominant_colors"][:3]]
        col = " and ".join(col_names) if col_names else ""
        bright = analysis["brightness"] if analysis["brightness"] != "unknown" else ""
        is_video = analysis["file_type"] == "video"

        # Build scene description from colors + brightness
        if bright == "dark" or bright == "very dark":
            depth = random.choice(["deep", "dark", "moody", "atmospheric"])
        elif bright == "bright" or bright == "very bright":
            depth = random.choice(["light", "bright", "airy", "clear", "soft"])
        else:
            depth = random.choice(["soft", "vibrant", "smooth", "natural", "minimal"])

        # Scene backdrop constructions
        if col:
            bg = random.choice([
                f"a {depth} {col} background",
                f"a {col} {depth} backdrop",
                f"a {depth} {col} sky",
                f"a {col} {depth} atmosphere",
            ])
            scene_in = random.choice([
                f"in a {depth} {col} atmosphere",
                f"against a {col} {depth} backdrop",
                f"across a {depth} {col} background",
                f"in a {col} {depth} setting",
            ])
            col_prefix = col.title() + " "
        else:
            bg = f"a {depth} background"
            scene_in = f"in a {depth} atmosphere"
            col_prefix = ""

        templates = []

        if is_video:
            # Pattern: "Animated [adj] [subject] [verb-ing] on [scene]"
            templates.append(f"Animated {col_prefix}{base} on {bg}")
            templates.append(f"Animated {col_prefix}{base} floating and drifting on {bg}")
            templates.append(f"Seamless loop of animated {col_prefix}{base} on {bg}")
            templates.append(f"Motion sequence of {col_prefix}{base} {scene_in}")
            templates.append(f"Animated overlay of {col_prefix}{base} on {bg}")

        else:
            templates.append(f"Beautiful {col_prefix}{base} with natural lighting on {bg}")
            templates.append(f"Stunning view of {col_prefix}{base} {scene_in}")
            templates.append(f"{col_prefix}{base.title()} captured in {depth} natural light on {bg}")
            templates.append(f"Serene {col_prefix}{base} landscape on {bg}")
            if analysis["orientation"] == "landscape":
                templates.append(f"Wide angle view of {col_prefix}{base} across {bg}")

        return random.sample(templates, min(count, len(templates)))

    def _generate_file_descriptions(self, base_concept, analysis, keywords, platform, count=1):
        base = base_concept.title() if base_concept else "Stock Image"
        ft = analysis["file_type"].title() if analysis["file_type"] != "unknown" else "Image"
        kw_sample = ", ".join(keywords[:12])
        dim = f"{analysis['width']}x{analysis['height']}" if analysis["width"] else "high resolution"
        platform_name = platform

        templates = [
            f"Discover this stunning {base} {ft}. Perfect for creative projects, "
            f"marketing materials, and commercial use on {platform_name}. "
            f"Features {kw_sample}. Ideal for designers, content creators, "
            f"and businesses seeking professional visual content. "
            f"Resolution: {dim}. Royalty-free license included.",

            f"Explore our premium {base} {ft} collection. "
            f"This versatile {ft.lower()} features {kw_sample}, "
            f"making it perfect for websites, social media, presentations, and print materials. "
            f"High-resolution format ({dim}) ensures crystal clear quality. "
            f"Download instantly and use immediately in your creative projects.",

            f"Professional {base} {ft} for your creative needs. "
            f"This {ft.lower()} captures the essence of {kw_sample}. "
            f"Perfect for advertising, branding, web design, and editorial content. "
            f"Resolution: {dim}. Enhanced and optimized for immediate use. "
            f"Compatible with all major design software and platforms.",

            f"Beautiful {base} {ft} showcasing {kw_sample}. "
            f"This royalty-free {ft.lower()} is perfect for both personal and commercial projects. "
            f"Features stunning composition, vibrant colors, and professional quality. "
            f"Resolution: {dim}. Available for instant download.",

            f"Captivating {base} {ft} featuring {kw_sample}. "
            f"This versatile visual asset is perfect for creative professionals, "
            f"marketers, and business owners. Resolution: {dim}. "
            f"Includes standard royalty-free license for {platform_name}."
        ]

        return random.sample(templates, min(count, len(templates)))

    def get_platform_csv_headers(self, platform="Adobe Stock"):
        return ["filename", "title", "keywords", "category"]

    def get_platform_csv_row(self, row_data, platform="Adobe Stock"):
        return {
            "filename": row_data.get("filename", ""),
            "title": row_data.get("title", ""),
            "keywords": row_data.get("keywords", ""),
            "category": row_data.get("category", "1")
        }

    def move_file_with_rename(self, source_path, dest_dir, new_name=None):
        src = Path(source_path)
        if not src.exists():
            raise FileNotFoundError(f"Source not found: {source_path}")
        dest = Path(dest_dir)
        dest.mkdir(parents=True, exist_ok=True)
        if new_name:
            new_filename = f"{new_name}{src.suffix}"
        else:
            new_filename = src.name
        dest_path = dest / new_filename
        if dest_path.exists():
            base = dest_path.stem
            counter = 1
            while dest_path.exists():
                dest_path = dest / f"{base}_{counter}{dest_path.suffix}"
                counter += 1
        src.rename(dest_path)
        return str(dest_path)

    def copy_file_with_rename(self, source_path, dest_dir, new_name=None):
        src = Path(source_path)
        if not src.exists():
            raise FileNotFoundError(f"Source not found: {source_path}")
        dest = Path(dest_dir)
        dest.mkdir(parents=True, exist_ok=True)
        import shutil
        if new_name:
            new_filename = f"{new_name}{src.suffix}"
        else:
            new_filename = src.name
        dest_path = dest / new_filename
        if dest_path.exists():
            base = dest_path.stem
            counter = 1
            while dest_path.exists():
                dest_path = dest / f"{base}_{counter}{dest_path.suffix}"
                counter += 1
        shutil.copy2(src, dest_path)
        return str(dest_path)

    def scan_directory(self, directory_path):
        supported = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff",
                     ".svg", ".ai", ".eps", ".mp4", ".mov", ".avi"}
        results = []
        d = Path(directory_path)
        if not d.is_dir():
            return results
        for f in sorted(d.iterdir()):
            if f.is_file() and f.suffix.lower() in supported:
                results.append({
                    "path": str(f),
                    "name": f.name,
                    "stem": f.stem,
                    "ext": f.suffix.lower(),
                    "type": FILE_CATEGORIES.get(f.suffix.lower(), "unknown"),
                    "size_kb": round(f.stat().st_size / 1024, 1)
                })
        return results

    def _guess_category(self, base_word):
        base = base_word.lower()
        best_cat = "Other"
        best_score = 0
        for cat_name, cat_data in self.db.items():
            all_terms = cat_data.get("aliases", []) + cat_data.get("synonyms", [])
            for subcat, items in cat_data.get("subjects", {}).items():
                all_terms.extend(items)
            for field in ["times", "seasons", "colors", "moods", "formats", "styles"]:
                if field in cat_data:
                    all_terms.extend(cat_data[field])
            for term in all_terms:
                tl = term.lower()
                if base == tl:
                    return cat_name.title()
                if base in tl:
                    score = len(base) / len(tl)
                    if score > best_score:
                        best_score = score
                        best_cat = cat_name.title()
                elif tl in base:
                    score = len(tl) / len(base)
                    if score > best_score:
                        best_score = score
                        best_cat = cat_name.title()
        return best_cat
