package main

import (
	"embed"
	"log"
	"net/http"
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
	f, err := sound.Open("rowing_boat_sound.mp3")
	if err != nil {
		log.Panicf("error opening sound file: %v", err)
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

	log.Fatal(http.ListenAndServe(":8080", nil))
}
