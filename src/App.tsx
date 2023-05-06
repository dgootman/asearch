import React, { useEffect, useState } from "react"
import { Container } from "react-bootstrap"

export const App = () => {
    const [pong, setPong] = useState({ pong: false })

    useEffect(() => {
        const fetchPing = async () => {
            const pingResult = await fetch("/api/ping")
            setPong(await pingResult.json())
        }

        fetchPing()
    }, [])


    return <Container>
        <h1>Hello World!</h1>
        Ping =&gt; {pong.pong ? "Pong" : "Wait for it..."}
    </Container>
}