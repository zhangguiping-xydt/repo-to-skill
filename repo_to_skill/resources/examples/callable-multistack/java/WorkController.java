package com.example.api;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/work")
public class WorkController {

    @PostMapping("/calculate")
    public WorkResult calculate(@RequestBody WorkRequest request) {
        return service.calculate(request);
    }
}
