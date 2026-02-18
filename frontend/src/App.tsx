import React, { useState, useCallback } from "react";
import { Toolbar } from "@/components/Layout/Toolbar";
import { Sidebar } from "@/components/Layout/Sidebar";
import { SplitPane } from "@/components/Layout/SplitPane";
import { PromptInput } from "@/components/Prompt/PromptInput";
import { AIExplanation } from "@/components/Prompt/AIExplanation";
import { DiagramCanvas } from "@/components/Canvas/DiagramCanvas";
import { useDiagramStore } from "@/stores/diagramStore";
import { useCodeStore } from "@/stores/codeStore";
import { useSessionStore } from "@/stores/sessionStore";
import { apiClient } from "@/services/apiClient";
import type { PromptResponse } from "@/types/api";
import type { DiagramNode, DiagramEdge, DiagramCluster } from "@/types/diagram";

const App: React.FC = () => {
  const [aiExplanation, setAiExplanation] = useState("");
  const [aiAssumptions, setAiAssumptions] = useState<string[]>([]);
  const [aiWarnings, setAiWarnings] = useState<string[]>([]);
  const [aiModel, setAiModel] = useState("");

  const setGraphModel = useDiagramStore((s) => s.setGraphModel);
  const setSourceCode = useCodeStore((s) => s.setSourceCode);
  const { isLoading, setLoading, setDiagramId } = useSessionStore();

  const handlePromptSubmit = useCallback(
    async (prompt: string) => {
      setLoading(true);
      try {
        const response: PromptResponse = await apiClient.generateFromPrompt({
          prompt,
        });

        // Update code store
        setSourceCode(response.diagram.source_code || "");

        // Update diagram ID
        setDiagramId(response.diagram.id);

        // Update AI explanation
        setAiExplanation(response.explanation);
        setAiAssumptions(response.assumptions);
        setAiWarnings(response.warnings);
        setAiModel(response.model_used);

        // Parse generated code into graph model (simplified — full parser in Phase 4)
        // For now, set an empty graph model until the render result arrives
        setGraphModel({ nodes: [], edges: [], clusters: [] });
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to generate diagram";
        setAiWarnings([message]);
      } finally {
        setLoading(false);
      }
    },
    [setGraphModel, setSourceCode, setLoading, setDiagramId],
  );

  return (
    <div className="flex h-screen flex-col">
      <Toolbar />
      <main className="flex flex-1 overflow-hidden">
        <Sidebar>
          <PromptInput onSubmit={handlePromptSubmit} isLoading={isLoading} />
          <AIExplanation
            explanation={aiExplanation}
            assumptions={aiAssumptions}
            warnings={aiWarnings}
            modelUsed={aiModel}
          />
        </Sidebar>
        <SplitPane
          left={
            <div className="flex h-full items-center justify-center bg-gray-50 p-4">
              <pre className="max-h-full max-w-full overflow-auto whitespace-pre-wrap text-xs text-gray-600">
                {useCodeStore.getState().sourceCode ||
                  "// Generated code will appear here"}
              </pre>
            </div>
          }
          right={<DiagramCanvas />}
        />
      </main>
    </div>
  );
};

export default App;
