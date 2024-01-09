// Run paddle.py with the configured environment.
// The configuration is read from the file `config.json`.
package run_paddle

import (
	"encoding/json"
	"log"
	"os"
	"os/exec"
	"path"
	"path/filepath"
)

type Config struct {
	// The path to the Python executable.
	Python string `json:"python"`
	// The path to the Python script.
	Script string `json:"script"`
	// The PATH environment variable to use.
	Path string `json:"path"`
}

func main() {
	// Read the configuration.
	commandPath, err := os.Executable()
	if err != nil {
		log.Fatal(err)
	}

	commandDir := filepath.Dir(commandPath)

	// Change the working directory.
	err = os.Chdir(commandDir)
	if err != nil {
		log.Fatal(err)
	}

	config := readConfig(path.Join(commandDir, "config.json"))

	// Run the Python script.
	runPython(config)
}

func readConfig(path string) Config {
	// Read the configuration file.
	file, err := os.Open(path)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	// Decode the configuration file.
	decoder := json.NewDecoder(file)
	config := Config{}
	err = decoder.Decode(&config)
	if err != nil {
		log.Fatal(err)
	}

	return config
}

func runPython(config Config) {
	// Create the command.
	cmd := createCommand(config)

	// Run the command.
	out, err := cmd.CombinedOutput()
	if err != nil {
		log.Println(string(out))
		log.Fatal(err)
	}
}

func createCommand(config Config) *exec.Cmd {
	python := filepath.Clean(os.ExpandEnv(config.Python))
	script := filepath.Clean(os.ExpandEnv(config.Script))
	// Create the command.
	cmd := exec.Command(python, script)

	log.Printf("Running %s %s", python, script)

	// Set the PATH environment variable.
	cmd.Env = []string{config.Path}

	return cmd
}
