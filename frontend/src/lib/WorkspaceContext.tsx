import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { getPlants } from "./api";

interface WorkspaceContextType {
  plantId: string;
  setPlantId: (id: string) => void;
  plants: string[];
}

const WorkspaceContext = createContext<WorkspaceContextType>({
  plantId: "DEMO-PLANT",
  setPlantId: () => {},
  plants: [],
});

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [plantId, setPlantId] = useState(() => {
    const saved = localStorage.getItem("plantos_plant_id");
    return saved || "DEMO-PLANT";
  });
  const [plants, setPlants] = useState<string[]>(["DEMO-PLANT"]);

  // Fetch plants on mount (does not depend on auth token)
  useEffect(() => {
    const fetchPlants = () => {
      getPlants()
        .then((data) => {
          const ids = data.map((p: any) => p.plant_id);
          if (ids.length > 0) {
            setPlants(ids);
            const saved = localStorage.getItem("plantos_plant_id");
            if (saved && ids.includes(saved)) {
              setPlantId(saved);
            } else {
              setPlantId(ids[0]);
            }
          }
        })
        .catch((err) => console.warn("Failed to fetch plants:", err));
    };
    fetchPlants();
    window.addEventListener("auth-login", fetchPlants);
    return () => window.removeEventListener("auth-login", fetchPlants);
  }, []);

  const handleSetPlantId = (id: string) => {
    setPlantId(id);
    localStorage.setItem("plantos_plant_id", id);
  };

  return (
    <WorkspaceContext.Provider value={{ plantId, setPlantId: handleSetPlantId, plants }}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  return useContext(WorkspaceContext);
}
