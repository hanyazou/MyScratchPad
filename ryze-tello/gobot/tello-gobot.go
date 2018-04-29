package main
 
import (
    "fmt"
    "gobot.io/x/gobot"
    "gobot.io/x/gobot/platforms/dji/tello"
    "gobot.io/x/gobot/platforms/joystick"
    "os/exec"
    "sync/atomic"
    "time"
)
 
type pair struct {
    x float64
    y float64
}
 
var leftX, leftY, rightX, rightY atomic.Value
 
const offset = 32767.0
 
func main() {
    drone := tello.NewDriver("8890")
    joystickAdaptor := joystick.NewAdaptor()
    stick := joystick.NewDriver(joystickAdaptor, "dualshock4")
 
    work := func() {
        leftX.Store(float64(0.0))
        leftY.Store(float64(0.0))
        rightX.Store(float64(0.0))
        rightY.Store(float64(0.0))
        mplayer := exec.Command("mplayer", "-fps", "35", "-")
        mplayerIn, _ := mplayer.StdinPipe()
        if err := mplayer.Start(); err != nil {
            fmt.Println(err)
            return
        }
 
        drone.On(tello.ConnectedEvent, func(data interface{}) {
            fmt.Println("Connected")
            drone.StartVideo()
            drone.SetVideoEncoderRate(4)
            gobot.Every(100*time.Millisecond, func() {
                drone.StartVideo()
            })
        })
 
        drone.On(tello.VideoFrameEvent, func(data interface{}) {
            pkt := data.([]byte)
            if _, err := mplayerIn.Write(pkt); err != nil {
                fmt.Println(err)
            }
        })
 
        stick.On(joystick.SquarePress, func(data interface{}) {
            fmt.Println("SquarePress")
            drone.BackFlip()
        })
 
        stick.On(joystick.TriangleRelease, func(data interface{}) {
            fmt.Println("TakeOff")
            drone.TakeOff()
        })
        stick.On(joystick.CirclePress, func(data interface{}) {
            fmt.Println("Land")
            drone.Land()
        })
        stick.On(joystick.LeftX, func(data interface{}) {
            val := float64(data.(int16))
            leftX.Store(val)
        })
        stick.On(joystick.LeftY, func(data interface{}) {
            val := float64(data.(int16))
            leftY.Store(val)
        })
        stick.On(joystick.RightX, func(data interface{}) {
            val := float64(data.(int16))
            rightX.Store(val)
        })
        stick.On(joystick.RightY, func(data interface{}) {
            val := float64(data.(int16))
            rightY.Store(val)
        })
        gobot.Every(10*time.Millisecond, func() {
            rightStick := getRightStick()
 
            switch {
            case rightStick.y < -10:
                drone.Forward(tello.ValidatePitch(rightStick.y, offset))
            case rightStick.y > 10:
                drone.Backward(tello.ValidatePitch(rightStick.y, offset))
            default:
                drone.Forward(0)
            }
 
            switch {
            case rightStick.x > 10:
                drone.Right(tello.ValidatePitch(rightStick.x, offset))
            case rightStick.x < -10:
                drone.Left(tello.ValidatePitch(rightStick.x, offset))
            default:
                drone.Right(0)
            }
        })
 
        gobot.Every(10*time.Millisecond, func() {
            leftStick := getLeftStick()
            switch {
            case leftStick.y < -10:
                drone.Up(tello.ValidatePitch(leftStick.y, offset))
            case leftStick.y > 10:
                drone.Down(tello.ValidatePitch(leftStick.y, offset))
            default:
                drone.Up(0)
            }
 
            switch {
            case leftStick.x > 20:
                drone.Clockwise(tello.ValidatePitch(leftStick.x, offset))
            case leftStick.x < -20:
                drone.CounterClockwise(tello.ValidatePitch(leftStick.x, offset))
            default:
                drone.Clockwise(0)
            }
        })
 
    }
 
    robot := gobot.NewRobot("tello",
        []gobot.Connection{joystickAdaptor},
        []gobot.Device{drone, stick},
        work,
    )
 
    robot.Start()
}
 
func getLeftStick() pair {
    s := pair{x: 0, y: 0}
    s.x = leftX.Load().(float64)
    s.y = leftY.Load().(float64)
    return s
}
 
func getRightStick() pair {
    s := pair{x: 0, y: 0}
    s.x = rightX.Load().(float64)
    s.y = rightY.Load().(float64)
    return s
}
