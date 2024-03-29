package main

import (
	"embed"
	"io/fs"
	"log"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/gopxl/beep"
	"github.com/gopxl/beep/mp3"
	"github.com/gopxl/beep/speaker"
)

//go:embed rowing_boat_sound.mp3
var sound embed.FS

type Message int

const (
	RowStart Message = iota
	RowStop
)

func soundDaemon(playingChan chan bool) {
	// if a mp3 file is found in the directory this program exists in, it will be used.
	commandPath, err := os.Executable()
	if err != nil {
		log.Panicf("error getting executable path: %v", err)
	}

	commandDir := filepath.Dir(commandPath)

	var f fs.File

	// search mp3 file in the directory this program exists in
	files, err := os.ReadDir(commandDir)
	if err != nil {
		log.Panicf("error reading directory: %v", err)
	}
	mp3File := "rowing_boat_sound.mp3"
	for _, file := range files {
		if file.IsDir() {
			continue
		}
		if filepath.Ext(file.Name()) == ".mp3" {
			mp3File = file.Name()
			break
		}
	}

	if f, err = os.Open(filepath.Join(commandDir, mp3File)); err != nil {
		f, err = sound.Open("rowing_boat_sound.mp3")
		if err != nil {
			log.Panicf("error opening sound file: %v", err)
		}
	}

	defer f.Close()

	streamer, format, err := mp3.Decode(f)
	if err != nil {
		log.Panicf("error decoding sound file: %v", err)
	}
	defer streamer.Close()

	err = speaker.Init(format.SampleRate, format.SampleRate.N(time.Second/10))
	if err != nil {
		log.Panicf("error initializing speaker: %v", err)
	}

	isPlaying := false

	for {
		select {
		case isPlaying = <-playingChan:
		default:
		}

		if isPlaying {
			log.Printf("start playing sound")
			done := make(chan bool)
			speaker.Play(beep.Seq(streamer, beep.Callback(func() {
				err := streamer.Seek(0)
				if err != nil {
					log.Panicf("error seeking sound file: %v", err)
				}
				done <- true
			})))
			<-done
			log.Printf("stop playing sound")
		}
	}
}

// dispatchSound plays a sound when the paddle is moving.
func dispathDaemon(c chan Message) {
	playingChan := make(chan bool)
	go soundDaemon(playingChan)

	for {
		msg := <-c
		switch msg {
		case RowStart:
			log.Printf("start rowing")
			playingChan <- true
		case RowStop:
			log.Printf("stop rowing")
			playingChan <- false
		}
	}
}

func getLocalIPs() ([]net.IP, error) {
	var ips []net.IP
	addresses, err := net.InterfaceAddrs()
	if err != nil {
		return nil, err
	}

	for _, address := range addresses {
		if ipnet, ok := address.(*net.IPNet); ok && !ipnet.IP.IsLoopback() {
			if ipnet.IP.To4() != nil {
				ips = append(ips, ipnet.IP)
			}
		}
	}

	return ips, nil
}

func main() {
	c := make(chan Message)
	go dispathDaemon(c)
	http.HandleFunc("/start", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("/start")
		c <- RowStart
	})
	http.HandleFunc("/stop", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("/stop")
		c <- RowStop
	})

	ips, err := getLocalIPs()
	if err != nil {
		log.Panicf("error getting local IPs: %v", err)
	}

	for _, ip := range ips {
		log.Printf("listening on http://%v:8080", ip)
	}

	log.Fatal(http.ListenAndServe(":8080", nil))
}
