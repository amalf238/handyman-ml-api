import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
from geopy.distance import geodesic
from sentence_transformers import SentenceTransformer
import logging
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class HandymanMLSystem:
    """Complete ML system for handyman recommendations"""
    
    def __init__(self):
        logger.info("Initializing HandymanMLSystem...")
        self.dataset = None
        self.sentence_model = None
        self.service_classifier = None
        self.label_encoder = None
        self.location_data = None
        self.location_embeddings = None
        self.location_names = None
        self.trained = False
        
        # For tracking last predictions
        self.last_detected_service = None
        self.last_detected_location = None
    
    def load_dataset_from_dict(self, dataset: Dict[str, Any]):
        """Load handyman dataset from dictionary"""
        try:
            self.dataset = dataset
            logger.info(f"Dataset loaded: {len(self.dataset.get('workers', []))} workers")
        except Exception as e:
            logger.error(f"Error loading dataset: {str(e)}")
            raise
    
    def load_dataset_from_file(self, dataset_path: str):
        """Load handyman dataset from file"""
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                self.dataset = json.load(f)
            logger.info(f"Dataset loaded: {len(self.dataset.get('workers', []))} workers")
        except Exception as e:
            logger.error(f"Error loading dataset from {dataset_path}: {str(e)}")
            raise
    
    def train_system(self):
        """Train the complete ML system"""
        try:
            logger.info("Training ML system...")
            
            # Initialize sentence transformer
            logger.info("Loading sentence transformer model...")
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Train service classifier
            logger.info("Training service classifier...")
            self._train_service_classifier()
            
            # Train location model
            logger.info("Training location model...")
            self._train_location_model()
            
            self.trained = True
            logger.info("ML system training completed successfully")
            
        except Exception as e:
            logger.error(f"Error training ML system: {str(e)}")
            raise
    
    def _train_service_classifier(self):
        """Train service type classifier"""
        # Training data for service classification
        service_training_examples = {
            'plumbing': [
                'water is dripping from my bathroom faucet constantly',
                'toilet keeps overflowing and making a huge mess',
                'kitchen sink drain is completely blocked',
                'shower has no water pressure at all',
                'water heater stopped working no hot water',
                'pipe burst in basement flooding area',
                'bathroom sink leaking underneath',
                'toilet not flushing properly waste backing up',
                'water pressure extremely low throughout house',
                'drain making gurgling sounds and smells terrible',
                'faucet handle broken cannot turn water on or off',
                'water bill very high suspect underground leak'
            ],
            'electrical': [
                'lights keep flickering throughout entire house',
                'power outlet stopped working completely',
                'circuit breaker keeps tripping shutting off power',
                'electrical switch making loud sparking sounds',
                'half the house has no electricity sudden power loss',
                'ceiling fan stopped working motor grinding noise',
                'electrical wiring looks old and potentially hazardous',
                'light fixtures need professional installation help',
                'power surges damaging electronic devices frequently',
                'electrical panel needs upgrade current one very old',
                'outlets not working in kitchen cannot use appliances',
                'electrical safety inspection needed for insurance'
            ],
            'appliance_repair': [
                'washing machine not spinning clothes staying wet',
                'dryer making extremely loud rattling noises',
                'dishwasher not cleaning dishes properly leaves residue',
                'refrigerator not keeping food cold temperature rising',
                'microwave stopped heating food completely broken',
                'oven temperature not working correctly burning food',
                'washing machine leaking water all over room',
                'appliance technician needed for equipment repair',
                'home appliances malfunctioning need professional diagnosis',
                'kitchen equipment not functioning properly needs fixing',
                'laundry machines broken down need immediate repair',
                'appliance maintenance service required for warranty'
            ],
            'ac_repair': [
                'air conditioner stopped cooling room getting hot',
                'ac unit making strange grinding mechanical noises',
                'aircon leaking water onto floor creating puddles',
                'central air system not working properly uneven cooling',
                'air conditioning blowing warm air instead of cold',
                'ac remote control not responding need manual repair',
                'hvac system needs professional maintenance check',
                'cooling system completely broken during hot weather',
                'air conditioner filter needs replacement service',
                'central cooling not reaching upstairs rooms properly',
                'ac compressor making loud noises need diagnosis',
                'air conditioning installation needed for new room'
            ],
            'masonry': [
                'need to build a wall in my kitchen area',
                'construct new brick wall for room separation',
                'stone wall construction needed for garden area',
                'build retaining wall for landscaping project',
                'construct bathroom wall with proper materials',
                'need professional to build kitchen counter wall',
                'build outdoor wall for privacy and security',
                'concrete wall construction needed for basement',
                'brick wall repair and reconstruction required',
                'build decorative stone wall for entrance',
                'wall construction needed for home addition',
                'masonry work needed for structural wall building'
            ],
            'painting': [
                'living room walls need fresh paint job badly',
                'exterior house paint peeling off needs refinishing',
                'bedroom walls need complete color change makeover',
                'ceiling paint cracking and falling need repair',
                'interior painting needed throughout entire house',
                'wall surface preparation and professional painting required',
                'complete house painting project needed inside and out',
                'professional painter needed for multiple rooms',
                'paint job required for home renovation project',
                'wall refinishing needed due to water damage',
                'exterior painting needed before selling house',
                'interior design painting project professional help'
            ],
            'cleaning': [
                'house needs thorough deep cleaning service badly',
                'post construction cleanup required extensive mess',
                'office space needs professional cleaning service',
                'carpet cleaning and stain removal service needed',
                'window cleaning service needed building wide',
                'bathroom deep cleaning required professional help',
                'kitchen cleaning and sanitization service needed',
                'move in cleaning service needed new house',
                'spring cleaning service needed entire property',
                'commercial cleaning service required for office',
                'post party cleanup service needed immediately',
                'house cleaning service needed regular maintenance'
            ],
            'general_maintenance': [
                'house needs comprehensive maintenance check multiple issues',
                'various small repairs needed around home property',
                'property upkeep and general maintenance service required',
                'handyman needed for multiple different household fixes',
                'general repair work needed throughout entire building',
                'home maintenance service required for aging property',
                'building needs comprehensive repairs before inspection',
                'various household problems need professional fixing',
                'property maintenance contract needed for ongoing care',
                'general handyman work required for multiple rooms',
                'house maintenance checklist items need completion',
                'property care and upkeep service needed regularly'
            ],
            'carpentry': [
                'kitchen cabinet door broken hanging off hinges',
                'wooden table leg wobbly unstable needs repair',
                'custom shelving installation needed for storage',
                'furniture repair and restoration professional service',
                'door frame damaged needs fixing properly',
                'wooden stairs making loud creaking sounds',
                'cabinet making and installation service required',
                'furniture assembly service required professional help',
                'wood work needed for home renovation project',
                'custom carpentry work needed for built ins',
                'furniture refinishing service needed antique pieces',
                'wooden deck repair needed professional assessment'
            ],
            'gardening': [
                'lawn grass overgrown and messy needs cutting',
                'garden plants need professional care and maintenance',
                'tree branches need trimming professional service',
                'landscape design and maintenance service required',
                'lawn mowing service required regular maintenance',
                'garden cleanup needed after storm damage',
                'plant care and fertilization service needed',
                'outdoor space needs professional landscaping help',
                'yard maintenance service needed overgrown property',
                'garden design consultation needed professional advice',
                'lawn care service needed regular weekly maintenance',
                'landscaping project needed complete yard makeover'
            ],
            'roofing': [
                'roof leaking badly during rain need repair',
                'roof tiles broken and missing after storm',
                'roof maintenance and inspection service needed',
                'gutter cleaning and repair service required',
                'roof replacement needed old tiles damaged',
                'roofing contractor needed for new installation',
                'roof waterproofing service needed urgently',
                'roof structure repair needed professional help',
                'roofing materials installation and replacement',
                'roof damage assessment needed after weather',
                'roof ventilation system needs professional work',
                'roofing project needed for home extension'
            ],
            'flooring': [
                'floor tiles broken and need replacement urgently',
                'wooden floor refinishing service needed badly',
                'floor installation needed for new room',
                'floor repair needed due to water damage',
                'flooring contractor needed for renovation project',
                'floor polishing and maintenance service required',
                'floor covering installation needed professional help',
                'floor leveling needed uneven surface',
                'floor restoration needed for old property',
                'flooring upgrade needed modern materials',
                'floor cleaning and sealing service required',
                'floor installation project needs professional work'
            ]
        }
        
        # Create training dataset
        training_data = []
        for service_type, examples in service_training_examples.items():
            for example in examples:
                training_data.append({
                    'text': example,
                    'service': service_type
                })
        
        training_df = pd.DataFrame(training_data)
        
        # Generate embeddings
        texts = training_df['text'].tolist()
        labels = training_df['service'].tolist()
        
        embeddings = self.sentence_model.encode(texts)
        
        # Encode labels
        self.label_encoder = LabelEncoder()
        encoded_labels = self.label_encoder.fit_transform(labels)
        
        # Train neural network
        self.service_classifier = MLPClassifier(
            hidden_layer_sizes=(256, 128, 64),
            activation='relu',
            solver='adam',
            max_iter=1500,
            random_state=42
        )
        
        self.service_classifier.fit(embeddings, encoded_labels)
        
        logger.info("Service classifier trained successfully")
    
    def _train_location_model(self):
        """Train location detection model"""
        self.location_data = {
            'colombo': (6.9271, 79.8612),
            'kandy': (7.2906, 80.6337),
            'galle': (6.0535, 80.2210),
            'negombo': (7.2084, 79.8380),
            'jaffna': (9.6615, 80.0255),
            'kurunegala': (7.4818, 80.3609),
            'anuradhapura': (8.3114, 80.4037),
            'matara': (5.9549, 80.5550),
            'ratnapura': (6.6828, 80.3992),
            'koswatta': (6.8875, 79.8800),
            'dehiwala': (6.8560, 79.8638),
            'mount lavinia': (6.8374, 79.8634),
            'moratuwa': (6.7730, 79.8816),
            'kotte': (6.8905, 79.9015),
            'nugegoda': (6.8649, 79.8997),
            'maharagama': (6.8482, 79.9298),
            'rajagiriya': (6.9084, 79.8916),
            'battaramulla': (6.8992, 79.9186),
            'malabe': (6.9147, 79.9731),
            'gampaha': (7.0873, 80.0014),
            'kalutara': (6.5854, 79.9607),
            'panadura': (6.7132, 79.9026),
            'kelaniya': (6.9553, 79.9192),
            'kaduwela': (6.9381, 79.9897),
            'pelawatta': (6.8461, 79.9062),
            'thalawathugoda': (6.8738, 79.9750),
            'homagama': (6.8441, 80.0022),
            'wattala': (6.9890, 79.8917),
            'ja ela': (7.0747, 79.8910),
            'kiribathgoda': (6.9804, 79.9297),
            'kottawa': (6.8207, 79.9097)
        }
        
        # Generate embeddings for locations
        self.location_names = list(self.location_data.keys())
        self.location_embeddings = self.sentence_model.encode(self.location_names)
        
        logger.info("Location model trained successfully")
    
    def predict_service(self, text: str) -> List[Tuple[str, float]]:
        """Predict service type from text"""
        if not self.trained:
            raise Exception("ML system not trained")
        
        embedding = self.sentence_model.encode([text])
        probabilities = self.service_classifier.predict_proba(embedding)[0]
        service_names = self.label_encoder.classes_
        
        # Get top predictions
        service_probs = list(zip(service_names, probabilities))
        service_probs.sort(key=lambda x: x[1], reverse=True)
        
        self.last_detected_service = service_probs[0][0]
        return service_probs[:3]
    
    def extract_location(self, text: str) -> Tuple[Tuple[float, float], str]:
        """Extract location from text"""
        if not self.trained:
            raise Exception("ML system not trained")
        
        text_embedding = self.sentence_model.encode([text])
        similarities = cosine_similarity(text_embedding, self.location_embeddings)[0]
        
        best_match_idx = np.argmax(similarities)
        best_similarity = similarities[best_match_idx]
        
        if best_similarity > 0.25:
            location_name = self.location_names[best_match_idx]
            coordinates = self.location_data[location_name]
            self.last_detected_location = location_name
            return coordinates, location_name
        else:
            self.last_detected_location = "colombo"
            return (6.9271, 79.8612), "colombo"
    
    def get_recommendations(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Get worker recommendations based on query"""
        if not self.trained:
            raise Exception("ML system not trained")
        
        logger.info(f"Processing query: {query}")
        
        try:
            # AI analysis
            service_predictions = self.predict_service(query)
            location_coords, location_name = self.extract_location(query)
            
            logger.info(f"Detected service: {service_predictions[0][0]} ({service_predictions[0][1]:.2%})")
            logger.info(f"Detected location: {location_name}")
            
            # Convert dataset to DataFrame
            if not self.dataset or 'workers' not in self.dataset:
                logger.error("Dataset not loaded properly")
                return []
            
            workers_df = pd.DataFrame(self.dataset['workers'])
            
            # Filter workers by predicted services
            likely_services = [s for s, p in service_predictions if p > 0.1]
            relevant_workers = workers_df[workers_df['service_type'].isin(likely_services)].copy()
            
            if len(relevant_workers) == 0:
                likely_services = [service_predictions[0][0]]
                relevant_workers = workers_df[workers_df['service_type'].isin(likely_services)].copy()
            
            if len(relevant_workers) == 0:
                logger.warning("No suitable workers found")
                return []
            
            # Score workers
            scored_workers = []
            for idx, worker in relevant_workers.iterrows():
                try:
                    # Service confidence score
                    service_confidence = next((p for s, p in service_predictions if s == worker['service_type']), 0)
                    service_score = service_confidence * 70
                    
                    # Distance score
                    worker_location = worker.get('location', {})
                    worker_lat = worker_location.get('latitude', 6.9271)
                    worker_lng = worker_location.get('longitude', 79.8612)
                    worker_coords = (worker_lat, worker_lng)
                    
                    distance = geodesic(location_coords, worker_coords).kilometers
                    distance_score = max(0, 20 - (distance * 0.2))
                    
                    # Quality score
                    rating = worker.get('rating', 0)
                    quality_score = (rating / 5.0) * 10
                    
                    total_score = service_score + distance_score + quality_score
                    
                    scored_workers.append({
                        'worker': worker,
                        'score': total_score,
                        'distance_km': distance,
                        'service_confidence': service_confidence
                    })
                    
                except Exception as e:
                    logger.warning(f"Error processing worker {worker.get('worker_id', 'unknown')}: {str(e)}")
                    continue
            
            # Sort by score
            scored_workers.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"Found {len(scored_workers)} workers, returning top {max_results}")
            return scored_workers[:max_results]
            
        except Exception as e:
            logger.error(f"Error in get_recommendations: {str(e)}")
            return []