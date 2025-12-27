"use client";

import { Users, Mail, FileText, Send, Sparkles, ChevronRight } from "lucide-react";

interface WelcomeScreenProps {
  onExampleClick: (example: string) => void;
}

const examples = [
  {
    title: "Search HubSpot Contacts",
    description: "Find contacts in your CRM",
    query: "Search for contacts in HubSpot",
    icon: Users,
  },
  {
    title: "Read Recent Emails",
    description: "Check your latest messages",
    query: "Show me recent emails",
    icon: Mail,
  },
  {
    title: "Create a Note",
    description: "Add notes to contacts or companies",
    query: "Create a note for contact 123 saying 'Followed up on pricing'",
    icon: FileText,
  },
  {
    title: "Send an Email",
    description: "Compose and send messages",
    query: "Send an email to john@example.com with subject 'Meeting'",
    icon: Send,
  },
];

export function WelcomeScreen({ onExampleClick }: WelcomeScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-6 py-12">
      <div className="max-w-2xl w-full space-y-8">
        {/* Logo/Header */}
        <div className="text-center space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-indigo-600 shadow-lg shadow-indigo-500/20 mb-4">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 dark:from-white dark:via-gray-100 dark:to-white bg-clip-text text-transparent">
            BridgeAI Chat
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Your AI assistant for managing business tools and integrations
          </p>
        </div>

        {/* Example Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-in fade-in slide-in-from-bottom-6 duration-700 delay-150">
          {examples.map((example, index) => {
            const Icon = example.icon;
            return (
              <button
                key={index}
                onClick={() => onExampleClick(example.query)}
                className="group relative p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm hover:border-indigo-300 dark:hover:border-indigo-700 hover:shadow-lg hover:shadow-indigo-500/10 transition-all duration-300 text-left"
              >
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                      {example.title}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {example.description}
                    </p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-indigo-500 group-hover:translate-x-1 transition-all flex-shrink-0 mt-1" />
                </div>
              </button>
            );
          })}
        </div>

        {/* Footer hint */}
        <p className="text-center text-sm text-gray-500 dark:text-gray-400 animate-in fade-in duration-1000 delay-300">
          Type a message below or click an example to get started
        </p>
      </div>
    </div>
  );
}
