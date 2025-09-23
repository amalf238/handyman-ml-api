import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../services/ai_chat_service.dart';
import 'search_results_screen.dart';

class AIChatScreen extends StatefulWidget {
  const AIChatScreen({super.key});

  @override
  _AIChatScreenState createState() => _AIChatScreenState();
}

class _AIChatScreenState extends State<AIChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final AIChatService _aiChatService = AIChatService();
  final ImagePicker _imagePicker = ImagePicker();
  List<ChatMessage> _messages = [];
  bool _isTyping = false;

  @override
  void initState() {
    super.initState();
    _initializeChat();
  }

  void _initializeChat() {
    _messages = [
      ChatMessage(
        text:
            'Hi! I\'m your AI assistant. I can help you find the right worker for any job. What do you need help with today?',
        isFromAI: true,
        timestamp: DateTime.now().subtract(const Duration(minutes: 1)),
      ),
    ];
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 1,
        title: const Text(
          'AI Chat',
          style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
        actions: [
          IconButton(
            icon: Icon(Icons.info_outline, color: Colors.grey[600]),
            onPressed: _showInfoDialog,
          ),
        ],
      ),
      body: Column(
        children: [
          _buildAIAssistantHeader(),
          _buildQuickActions(),
          Expanded(
            child: _messages.isEmpty
                ? _buildEmptyState()
                : _buildChatMessages(),
          ),
          _buildPhotoUploadSection(),
          _buildMessageInput(),
        ],
      ),
    );
  }

  Widget _buildAIAssistantHeader() {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.white,
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: const Color(0xFF2E86AB),
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Icon(Icons.smart_toy, color: Colors.white, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'AI Assistant',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                Text(
                  'Powered by ML models - Get personalized recommendations',
                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActions() {
    final quickActions = [
      {'title': 'Plumbing Issue', 'color': Colors.blue},
      {'title': 'Electrical Problem', 'color': Colors.orange},
      {'title': 'Cleaning Service', 'color': Colors.green},
      {'title': 'Emergency Repair', 'color': Colors.red},
    ];

    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.white,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Quick Actions:',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w500,
              color: Colors.grey[700],
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: quickActions
                .map(
                  (action) => _buildQuickActionChip(
                    action['title'] as String,
                    action['color'] as Color,
                  ),
                )
                .toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActionChip(String title, Color color) {
    return GestureDetector(
      onTap: () => _handleQuickAction(title),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Text(
          title,
          style: TextStyle(
            fontSize: 12,
            color: color,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Container(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.chat_bubble_outline, size: 64, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text(
            'Start a conversation',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Describe your issue or tap a quick action above',
            style: TextStyle(fontSize: 14, color: Colors.grey[500]),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildChatMessages() {
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.all(16),
      itemCount: _messages.length + (_isTyping ? 1 : 0),
      itemBuilder: (context, index) {
        if (index == _messages.length && _isTyping) {
          return _buildTypingIndicator();
        }
        return _buildMessageBubble(_messages[index]);
      },
    );
  }

  Widget _buildMessageBubble(ChatMessage message) {
    final isFromAI = message.isFromAI;
    final hasText = message.text != null && message.text!.trim().isNotEmpty;
    final hasImage = message.imageBytes != null;
    final hasSuggestions =
        message.suggestions != null && message.suggestions!.isNotEmpty;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: Row(
        mainAxisAlignment: isFromAI
            ? MainAxisAlignment.start
            : MainAxisAlignment.end,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (isFromAI) ...[
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: const Color(0xFF2E86AB),
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Icon(Icons.smart_toy, color: Colors.white, size: 16),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.75,
              ),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: isFromAI ? Colors.white : const Color(0xFF2E86AB),
                borderRadius: BorderRadius.circular(18).copyWith(
                  bottomLeft: isFromAI
                      ? const Radius.circular(4)
                      : const Radius.circular(18),
                  bottomRight: isFromAI
                      ? const Radius.circular(18)
                      : const Radius.circular(4),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (hasImage) ...[
                    ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.memory(
                        message.imageBytes!,
                        width: double.infinity,
                        height: 200,
                        fit: BoxFit.cover,
                      ),
                    ),
                    if (message.imageName != null &&
                        message.imageName!.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Text(
                        message.imageName!,
                        style: TextStyle(
                          color: isFromAI ? Colors.black54 : Colors.white70,
                          fontSize: 12,
                        ),
                      ),
                    ],
                    if (hasText) const SizedBox(height: 12),
                  ],
                  if (hasText)
                    Text(
                      message.text!,
                      style: TextStyle(
                        color: isFromAI ? Colors.black : Colors.white,
                        fontSize: 16,
                      ),
                    ),
                  if (hasSuggestions) ...[
                    SizedBox(height: hasText ? 12 : 4),
                    ...message.suggestions!.map(
                      (suggestion) => Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: GestureDetector(
                          onTap: () => _handleSuggestionTap(suggestion),
                          child: Container(
                            width: double.infinity,
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: const Color(0xFF2E86AB).withOpacity(0.1),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(
                                color: const Color(0xFF2E86AB).withOpacity(0.3),
                              ),
                            ),
                            child: Text(
                              suggestion,
                              style: const TextStyle(
                                color: Color(0xFF2E86AB),
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                  const SizedBox(height: 8),
                  Text(
                    _formatTime(message.timestamp),
                    style: TextStyle(
                      color: isFromAI
                          ? Colors.grey[500]
                          : Colors.white.withOpacity(0.7),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (!isFromAI) ...[
            const SizedBox(width: 8),
            CircleAvatar(
              backgroundColor: Colors.grey[300],
              radius: 16,
              child: const Icon(Icons.person, color: Colors.white, size: 16),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildTypingIndicator() {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: Row(
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: const Color(0xFF2E86AB),
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Icon(Icons.smart_toy, color: Colors.white, size: 16),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(
                18,
              ).copyWith(bottomLeft: const Radius.circular(4)),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 4,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: const [
                _TypingDot(),
                SizedBox(width: 4),
                _TypingDot(),
                SizedBox(width: 4),
                _TypingDot(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPhotoUploadSection() {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.white,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          border: Border.all(
            color: Colors.grey[300]!,
            style: BorderStyle.solid,
          ),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          children: [
            Icon(Icons.file_upload_outlined, size: 32, color: Colors.grey[500]),
            const SizedBox(height: 8),
            Text(
              'Upload issue photo for AI analysis',
              style: TextStyle(fontSize: 14, color: Colors.grey[600]),
            ),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: _handlePhotoUpload,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.white,
                side: const BorderSide(color: Color(0xFF2E86AB)),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              child: const Text(
                'Choose Photo',
                style: TextStyle(color: Color(0xFF2E86AB)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMessageInput() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 4,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            IconButton(
              icon: Icon(Icons.camera_alt, color: Colors.grey[600]),
              onPressed: _handleCameraCapture,
            ),
            IconButton(
              icon: Icon(Icons.mic, color: Colors.grey[600]),
              onPressed: _handleVoiceInput,
            ),
            Expanded(
              child: TextField(
                controller: _messageController,
                decoration: InputDecoration(
                  hintText: 'Describe your issue...',
                  filled: true,
                  fillColor: Colors.grey[100],
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(25),
                    borderSide: BorderSide.none,
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 10,
                  ),
                ),
                maxLines: null,
                onSubmitted: (text) => _sendMessage(),
              ),
            ),
            const SizedBox(width: 8),
            Container(
              decoration: const BoxDecoration(
                color: Color(0xFF2E86AB),
                shape: BoxShape.circle,
              ),
              child: IconButton(
                icon: const Icon(Icons.send, color: Colors.white),
                onPressed: _sendMessage,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showInfoDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('AI Assistant Info'),
        content: const Text(
          'This AI assistant uses advanced machine learning to understand your home service needs and recommend the best workers for your job.\n\n'
          'You can:\n'
          '• Type your issue description\n'
          '• Upload photos for AI analysis\n'
          '• Get personalized recommendations\n'
          '• View worker profiles and contact details',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Got it'),
          ),
        ],
      ),
    );
  }

  void _handleQuickAction(String action) {
    _messageController.text = 'I need help with: $action';
    _sendMessage();
  }

  Future<void> _handlePhotoUpload() async {
    await _pickAndAnalyzeImage(ImageSource.gallery);
  }

  Future<void> _handleCameraCapture() async {
    await _pickAndAnalyzeImage(ImageSource.camera);
  }

  void _handleVoiceInput() {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Voice input - Coming Soon!')));
  }

  Future<void> _sendMessage() async {
    final userMessage = _messageController.text.trim();
    if (userMessage.isEmpty) return;

    final historyPayload = _buildHistoryPayload();
    final message = ChatMessage(
      text: userMessage,
      isFromAI: false,
      timestamp: DateTime.now(),
    );

    setState(() {
      _messages.add(message);
      _isTyping = true;
    });

    _messageController.clear();
    _scrollToBottom();

    try {
      final responseText = await _aiChatService.sendTextMessage(
        message: userMessage,
        history: historyPayload,
      );

      if (!mounted) return;

      setState(() {
        _isTyping = false;
        _messages.add(
          ChatMessage(
            text: responseText,
            isFromAI: true,
            timestamp: DateTime.now(),
          ),
        );
      });
      _scrollToBottom(delay: const Duration(milliseconds: 200));
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _isTyping = false;
      });

      final errorMessage = error is AIChatException
          ? error.message
          : 'We were unable to reach the AI assistant. Please try again.';

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(errorMessage)));
    }
  }

  List<Map<String, dynamic>> _buildHistoryPayload() {
    final textMessages = _messages
        .where((m) => m.text != null && m.text!.isNotEmpty)
        .toList();

    final startIndex = textMessages.length > 10 ? textMessages.length - 10 : 0;

    return textMessages.sublist(startIndex).map((message) {
      return {
        'role': message.isFromAI ? 'assistant' : 'user',
        'content': message.text!,
      };
    }).toList();
  }

  Future<void> _pickAndAnalyzeImage(ImageSource source) async {
    try {
      final pickedFile = await _imagePicker.pickImage(
        source: source,
        imageQuality: 85,
      );

      if (pickedFile == null) return;

      final imageBytes = await pickedFile.readAsBytes();

      setState(() {
        _messages.add(
          ChatMessage(
            isFromAI: false,
            timestamp: DateTime.now(),
            imageBytes: imageBytes,
            imageName: pickedFile.name,
          ),
        );
        _isTyping = true;
      });

      _scrollToBottom();

      final analysis = await _aiChatService.analyzeImage(imageBytes);

      if (!mounted) return;

      setState(() {
        _isTyping = false;
        _messages.add(
          ChatMessage(
            text: analysis,
            isFromAI: true,
            timestamp: DateTime.now(),
            suggestions: const [
              'Find skilled workers for this issue',
              'Get DIY repair tips',
              'Search nearby contractors',
            ],
          ),
        );
      });
      _scrollToBottom(delay: const Duration(milliseconds: 200));
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _isTyping = false;
      });

      final errorMessage = error is AIChatException
          ? error.message
          : 'We were unable to analyze that image. Please try again.';

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(errorMessage)));
    }
  }

  void _scrollToBottom({Duration delay = const Duration(milliseconds: 100)}) {
    Future.delayed(delay, () {
      if (!_scrollController.hasClients) return;

      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    });
  }

  Future<void> _handleSuggestionTap(String suggestion) async {
    if (suggestion.contains('Find skilled workers') || 
        suggestion.contains('Search nearby contractors')) {
      // Use the ML API to get recommendations
      try {
        setState(() {
          _isTyping = true;
        });

        final workers = await _aiChatService.getWorkerRecommendations(
          query: AIChatService.lastImageDescription.isEmpty
              ? 'general maintenance'
              : AIChatService.lastImageDescription,
          maxResults: 5,
        );

        setState(() {
          _isTyping = false;
        });

        if (workers.isNotEmpty) {
          // Navigate to search results screen with workers
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => SearchResultsScreen(
                query: AIChatService.lastImageDescription,
                workers: workers, // Pass the workers directly
              ),
            ),
          );
        } else {
          // Show fallback message
          setState(() {
            _messages.add(
              ChatMessage(
                text: 'No workers found for this request. Please try describing your issue differently or contact us for manual assistance.',
                isFromAI: true,
                timestamp: DateTime.now(),
              ),
            );
          });
          _scrollToBottom(delay: const Duration(milliseconds: 200));
        }

      } catch (error) {
        setState(() {
          _isTyping = false;
        });

        final errorMessage = error is AIChatException
            ? 'ML service unavailable. Using fallback search...'
            : 'Error connecting to worker database. Please try again.';

        // Fallback to regular search if ML API fails
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => SearchResultsScreen(
              query: AIChatService.lastImageDescription.isEmpty
                  ? 'general'
                  : AIChatService.lastImageDescription,
            ),
          ),
        );

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(errorMessage)),
        );
      }

    } else if (suggestion.contains('DIY repair tips')) {
      // Get DIY tips from ChatGPT
      setState(() {
        _isTyping = true;
      });

      try {
        final tips = await _aiChatService.sendTextMessage(
          message:
              "Based on this issue: '${AIChatService.lastImageDescription}', suggest only safety checks and repair tips that a user can do at home themselves. Do not recommend hiring workers. Be specific, short, and practical.",
        );

        setState(() {
          _isTyping = false;
          _messages.add(
            ChatMessage(
              text: tips,
              isFromAI: true,
              timestamp: DateTime.now(),
            ),
          );
        });
        _scrollToBottom(delay: const Duration(milliseconds: 200));

      } catch (error) {
        setState(() {
          _isTyping = false;
        });

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Unable to get repair tips: ${error.toString()}')),
        );
      }

    } else {
      // Handle other suggestions
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$suggestion - Feature coming soon!')),
      );
    }
  }

  String _formatTime(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);

    if (difference.inDays > 0) {
      return '${difference.inDays}d ago';
    } else if (difference.inHours > 0) {
      return '${difference.inHours}h ago';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes}m ago';
    } else {
      return 'Just now';
    }
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();

    // Print the last stored description to terminal/CLI when leaving this screen
    if (AIChatService.lastImageDescription.isNotEmpty) {
      // ignore: avoid_print
      print('Last stored description: ${AIChatService.lastImageDescription}');
    }
    super.dispose();
  }
}

class _TypingDot extends StatelessWidget {
  const _TypingDot();

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 600),
      width: 8,
      height: 8,
      decoration: const BoxDecoration(
        color: Colors.grey,
        shape: BoxShape.circle,
      ),
    );
  }
}

class ChatMessage {
  final String? text;
  final bool isFromAI;
  final DateTime timestamp;
  final List<String>? suggestions;
  final Uint8List? imageBytes;
  final String? imageName;

  ChatMessage({
    required this.isFromAI,
    required this.timestamp,
    this.suggestions,
    this.text,
    this.imageBytes,
    this.imageName,
  });
}