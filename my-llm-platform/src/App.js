import React, { useState } from 'react';

// Main App component for the LLM query platform
const App = () => {
    // State to store the currently selected LLM
    const [selectedLLM, setSelectedLLM] = useState('gemini');
    // State to store the user's question
    const [question, setQuestion] = useState('');
    // State to store the response from the LLM
    const [response, setResponse] = useState('');
    // State to manage loading status during API calls
    const [isLoading, setIsLoading] = useState(false);
    // State to store any error messages
    const [errorMessage, setErrorMessage] = useState('');

    /**
     * Handles the submission of the user's question.
     * Based on the selected LLM, it either calls the Gemini API
     * or provides a placeholder response for GPT and Claude.
     * @param {object} event - The form submission event.
     */
    const handleSubmit = async (event) => {
        event.preventDefault(); // Prevent default form submission behavior

        if (!question.trim()) {
            setErrorMessage('Please enter a question.');
            return;
        }

        setIsLoading(true); // Set loading state to true
        setResponse(''); // Clear previous response
        setErrorMessage(''); // Clear previous error message

        try {
            if (selectedLLM === 'gemini') {
                // Gemini API call logic
                let chatHistory = [];
                chatHistory.push({ role: 'user', parts: [{ text: question }] });
                const payload = { contents: chatHistory };
                const apiKey = ""; // API key is provided by the environment

                const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`;

                const apiResponse = await fetch(apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!apiResponse.ok) {
                    const errorData = await apiResponse.json();
                    throw new Error(`API error: ${apiResponse.status} - ${errorData.message || 'Unknown error'}`);
                }

                const result = await apiResponse.json();

                if (result.candidates && result.candidates.length > 0 &&
                    result.candidates[0].content && result.candidates[0].content.parts &&
                    result.candidates[0].content.parts.length > 0) {
                    setResponse(result.candidates[0].content.parts[0].text);
                } else {
                    setResponse('No response from Gemini API or unexpected format.');
                }
            } else if (selectedLLM === 'gpt') {
                // Placeholder for GPT integration
                setResponse(`For GPT, you would integrate with the OpenAI API here.
                Example: You'd need to fetch from 'https://api.openai.com/v1/chat/completions' with your OpenAI API key and appropriate payload.`);
            } else if (selectedLLM === 'claude') {
                // Placeholder for Claude integration
                setResponse(`For Claude, you would integrate with the Anthropic API here.
                Example: You'd need to fetch from 'https://api.anthropic.com/v1/messages' with your Anthropic API key and appropriate payload.`);
            }
        } catch (error) {
            console.error('Error fetching data:', error);
            setErrorMessage(`Failed to get response: ${error.message}`);
        } finally {
            setIsLoading(false); // Set loading state to false
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-500 to-purple-600 p-4 sm:p-8 flex items-center justify-center font-sans">
            <div className="bg-white p-6 sm:p-10 rounded-2xl shadow-xl w-full max-w-2xl transform transition-all duration-300 hover:scale-105">
                <h1 className="text-3xl sm:text-4xl font-extrabold text-center text-gray-900 mb-6 tracking-tight">
                    Universal LLM Platform
                </h1>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* LLM Selection Dropdown */}
                    <div>
                        <label htmlFor="llm-select" className="block text-sm font-medium text-gray-700 mb-2">
                            Choose your LLM:
                        </label>
                        <div className="relative">
                            <select
                                id="llm-select"
                                value={selectedLLM}
                                onChange={(e) => setSelectedLLM(e.target.value)}
                                className="block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 text-base appearance-none transition duration-150 ease-in-out bg-white pr-10 cursor-pointer"
                            >
                                <option value="gemini">Gemini (Live Demo)</option>
                                <option value="gpt">GPT (Placeholder)</option>
                                <option value="claude">Claude (Placeholder)</option>
                            </select>
                            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                                <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                                </svg>
                            </div>
                        </div>
                    </div>

                    {/* Question Input Area */}
                    <div>
                        <label htmlFor="question-input" className="block text-sm font-medium text-gray-700 mb-2">
                            Your Question:
                        </label>
                        <textarea
                            id="question-input"
                            value={question}
                            onChange={(e) => setQuestion(e.target.value)}
                            rows="5"
                            className="block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 text-base resize-y placeholder-gray-400 transition duration-150 ease-in-out"
                            placeholder="e.g., What is the capital of France?"
                        ></textarea>
                    </div>

                    {/* Submit Button */}
                    <button
                        type="submit"
                        className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-lg font-semibold text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition duration-200 ease-in-out transform hover:-translate-y-0.5"
                        disabled={isLoading}
                    >
                        {isLoading ? (
                            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                        ) : (
                            'Ask LLM'
                        )}
                    </button>
                </form>

                {/* Response Display Area */}
                {(response || errorMessage) && (
                    <div className="mt-8 pt-6 border-t border-gray-200">
                        {errorMessage && (
                            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg relative mb-4" role="alert">
                                <strong className="font-bold">Error!</strong>
                                <span className="block sm:inline ml-2">{errorMessage}</span>
                            </div>
                        )}

                        {response && (
                            <div className="bg-purple-50 p-4 rounded-lg shadow-inner">
                                <h2 className="text-lg font-semibold text-purple-800 mb-3">Response:</h2>
                                <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{response}</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default App;