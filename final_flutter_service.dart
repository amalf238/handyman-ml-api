import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../config/api_keys.dart';

class AIChatException implements Exception {
  AIChatException(this.message);
  final String message;

  @override
  String toString() => 'AIChatException: $message';
}

class WorkerRecommendation {
  final String id;
  final String name;
  final String serviceType;
  final double rating;
  final int experienceYears;
  final int jobsCompleted;
  final Map<String, dynamic> location;
  final Map<String, dynamic> pricing;
  final Map<String, dynamic> contact;
  final Map<String, dynamic> availability;
  final Map<String, dynamic> profile;
  final double aiScore;
  final double distanceKm;
  final double serviceConfidence;

  WorkerRecommendation({
    required this.id,
    required this.name,
    required this.serviceType,
    required this.rating,
    required this.experienceYears,
    required this.jobsCompleted,
    required this.location,
    required this.pricing,
    required this.contact,
    required this.availability,
    required this.profile,
    required this.aiScore,
    required this.distanceKm,
    required this.serviceConfidence,
  });

  factory WorkerRecommendation.fromJson(Map<String, dynamic> json) {
    return WorkerRecommendation(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      serviceType: json['service_type'] ?? '',
      rating: (json['rating'] ?? 0.0).toDouble(),
      experienceYears: json['experience_years'] ?? 0,
      jobsCompleted: json['jobs_completed'] ?? 0,
      location: json['location'] ?? {},
      pricing: json['pricing'] ?? {},
      contact: json['contact'] ?? {},
      availability: json['availability'] ?? {},
      profile: json['profile'] ?? {},
      aiScore: (json['ai_score'] ?? 0.0).toDouble(),
      distanceKm: (json['distance_km'] ?? 0.0).toDouble(),
      serviceConfidence: (json['service_confidence'] ?? 0.0).toDouble(),
    );
  }
}

class AIChatService {
  AIChatService({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  // ChatGPT API configuration
  static const String _openAIApiUrl = 'https://api.openai.com/v1/chat/completions';
  static const String _model = 'gpt-4o-mini';

  // ML API configuration - REPLACE WITH YOUR RAILWAY URL
  static const String _mlApiBaseUrl = 'https://handyman-ml-api-production.railway.app';
  // Alternative for local testing: 'http://localhost:5000'

  static const String _systemPrompt =
      'You are FixMate, a helpful assistant who supports users with home service needs. Provide concise, clear, and friendly responses.';

  /// Default prompt used whenever an image is uploaded.
  String imageDescriptionPrompt =
      'Describe what you can see in this image in one sentence focusing on any issues or problems that need repair.';

  // Store the latest one-sentence description from image analysis
  static String lastImageDescription = "";

  // Keep a small history in-memory
  static final List<String> imageDescriptionHistory = <String>[];

  /// Send text message to ChatGPT
  Future<String> sendTextMessage({
    required String message,
    List<Map<String, dynamic>> history = const [],
  }) async {
    final messages = <Map<String, dynamic>>[
      {'role': 'system', 'content': _systemPrompt},
      ...history,
      {'role': 'user', 'content': message},
    ];

    final payload = <String, dynamic>{
      'model': _model,
      'messages': messages,
      'temperature': 0.3,
      'max_tokens': 600,
    };

    return _performOpenAIRequest(payload);
  }

  /// Analyze image with ChatGPT
  Future<String> analyzeImage(Uint8List imageBytes, {String? prompt}) async {
    final encodedImage = base64Encode(imageBytes);

    final messages = <Map<String, dynamic>>[
      {'role': 'system', 'content': _systemPrompt},
      {
        'role': 'user',
        'content': [
          {'type': 'text', 'text': prompt ?? imageDescriptionPrompt},
          {
            'type': 'image_url',
            'image_url': {'url': 'data:image/png;base64,$encodedImage'},
          },
        ],
      },
    ];

    final payload = <String, dynamic>{
      'model': _model,
      'messages': messages,
      'temperature': 0.3,
      'max_tokens': 300,
    };

    final result = await _performOpenAIRequest(payload);

    // Update the stored description
    lastImageDescription = result.trim();
    if (lastImageDescription.isNotEmpty) {
      imageDescriptionHistory.add(lastImageDescription);
      // Keep the history short (e.g., last 20)
      if (imageDescriptionHistory.length > 20) {
        imageDescriptionHistory.removeAt(0);
      }
    }

    return result;
  }

  /// Get worker recommendations from ML API
  Future<List<WorkerRecommendation>> getWorkerRecommendations({
    required String query,
    int maxResults = 5,
    String? location,
  }) async {
    try {
      final url = Uri.parse('$_mlApiBaseUrl/api/search-workers');
      
      final payload = {
        'query': query,
        'max_results': maxResults,
        if (location != null) 'location': location,
      };

      final response = await _client.post(
        url,
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode(payload),
      );

      if (response.statusCode != 200) {
        throw AIChatException(
          'ML API error (${response.statusCode}): ${response.body}',
        );
      }

      final Map<String, dynamic> data = jsonDecode(response.body);
      
      if (data['success'] != true) {
        throw AIChatException(
          data['error'] ?? 'Unknown error from ML API',
        );
      }

      final List<dynamic> workersJson = data['workers'] ?? [];
      return workersJson
          .map((json) => WorkerRecommendation.fromJson(json))
          .toList();

    } catch (e) {
      if (e is AIChatException) rethrow;
      throw AIChatException('Failed to get worker recommendations: $e');
    }
  }

  /// Get simplified worker recommendations for image descriptions
  Future<Map<String, dynamic>> analyzeImageDescription({
    required String description,
    String? location,
    int maxResults = 3,
  }) async {
    try {
      final url = Uri.parse('$_mlApiBaseUrl/api/analyze-image-description');
      
      final payload = {
        'description': description,
        'location': location ?? 'colombo',
        'max_results': maxResults,
      };

      final response = await _client.post(
        url,
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode(payload),
      );

      if (response.statusCode != 200) {
        throw AIChatException(
          'ML API error (${response.statusCode}): ${response.body}',
        );
      }

      final Map<String, dynamic> data = jsonDecode(response.body);
      
      if (data['success'] != true) {
        throw AIChatException(
          data['error'] ?? 'Unknown error from ML API',
        );
      }

      return data;

    } catch (e) {
      if (e is AIChatException) rethrow;
      throw AIChatException('Failed to analyze image description: $e');
    }
  }

  Future<String> _performOpenAIRequest(Map<String, dynamic> payload) async {
    final apiKey = ApiKeys.openAIApiKey.trim();
    if (apiKey.isEmpty || apiKey == 'YOUR_CHATGPT_API_KEY') {
      throw AIChatException(
        'Please add your ChatGPT API key to lib/config/api_keys.dart.',
      );
    }

    final response = await _client.post(
      Uri.parse(_openAIApiUrl),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $apiKey',
      },
      body: jsonEncode(payload),
    );

    if (response.statusCode >= 400) {
      throw AIChatException(
        'ChatGPT API error (${response.statusCode}): ${response.body}',
      );
    }

    final Map<String, dynamic> data = jsonDecode(response.body);
    final choices = data['choices'];
    if (choices is List && choices.isNotEmpty) {
      final msg = choices[0]['message'];
      if (msg is Map && msg['content'] is String) {
        return (msg['content'] as String).trim();
      }
      if (msg is Map && msg['content'] is List) {
        final parts = msg['content'] as List;
        final text = parts
            .whereType<Map>()
            .where((p) => p['type'] == 'text' && p['text'] is String)
            .map((p) => p['text'] as String)
            .join('\n')
            .trim();
        if (text.isNotEmpty) return text;
      }
    }

    throw AIChatException('The ChatGPT API did not return any text output.');
  }
}