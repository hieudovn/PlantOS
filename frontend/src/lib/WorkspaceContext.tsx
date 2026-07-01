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
  const [plantId, setPlantId] = useState("DEMO-PLANT");
  const [plants, setPlants] = useState<string[]>(["DEMO-PLANT"]);

  // Re-fetch plants when a new auth token appears (user logs in)
  const [tokenVersion, setTokenVersion] = useState(0);
  useEffect(() => {
    // Listen for auth token changes
    const check = () => {
      const t = localStorage.getItem("plantos_token");
      setTokenVersion(v => t ? v + 1 : 0);
    };
    check();
    window.addEventListener("storage", check);
    // Also check after login (custom event)
    window.addEventListener("auth-login", check);
    return () => {
      window.removeEventListener("storage", check);
      window.removeEventListener("auth-login", check);
    };
  }, []);

  useEffect(() => {
    if (!tokenVersion) return; // No token yet
    getPlants()
      .then((data) => {
        const ids = data.map((p: any) => p.plant_id);
        if (ids.length > 0) {
          setPlants(ids);
          if (!ids.includes(plantId)) {
            setPlantId(ids[0]);
          }
        }
      })
      .catch(() => {});
  }, [tokenVersion]); // Re-run when token changes

  return (
    <WorkspaceContext.Provider value={{ plantId, setPlantId, plants }}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  return useContext(WorkspaceContext);
}
